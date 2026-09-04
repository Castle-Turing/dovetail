# The show verb's end-to-end check, for the path the Nix sandbox can
# reach: `dovetail-show --socket <path>`.
#
# Steps two and three of the targeting rule need a compositor and a
# Wayland session, and the sandbox has neither — those are the two items
# on the human checklist at the end of `docs/show.md`. Step one needs
# only a live instance and a socket, which is exactly what the module
# guarantees, so it is checked here in full:
#
#   1. a headless instance is launched on some *other* file, so that a
#      buffer arriving is evidence of the verb and not of the launch;
#   2. `dovetail-show --socket ... note.md` loads note.md, confirmed by
#      asking the instance over RPC rather than by trusting exit codes;
#   3. `--line N` puts the cursor on line N;
#   4. `--print-socket` prints the socket it used, and nothing else;
#   5. a socket that does not answer fails loudly and names itself,
#      rather than silently opening the file somewhere else.
{
  lib,
  runCommand,
  neovim-unwrapped,
  dovetail-nvim,
  dovetail-show,
}:

runCommand "dovetail-show-explicit-socket"
  {
    nativeBuildInputs = [
      dovetail-nvim
      dovetail-show
    ];
    meta.description = "dovetail-show opens a file in the instance the caller named";
  }
  ''
    set -euo pipefail

    client="${lib.getExe' neovim-unwrapped "nvim"} --clean --headless"

    export HOME="$PWD/home"
    export XDG_RUNTIME_DIR="$PWD/run"
    mkdir -p "$HOME" "$XDG_RUNTIME_DIR"
    chmod 700 "$XDG_RUNTIME_DIR"

    # No terminal is configured on purpose: if the verb ever fell through
    # to launching, it would fail loudly here rather than quietly passing.
    unset DOVETAIL_TERMINAL TERMINAL DOVETAIL_SOCKET SWAYSOCK || true

    cat > other.md <<'EOF'
    # Not the file under test
    EOF

    cat > note.md <<'EOF'
    # A note

    Third line.
    Fourth line.
    Fifth line.
    EOF

    echo "--- launching a headless instance on another file"
    nvim --headless other.md </dev/null >nvim.log 2>&1 &
    nvim_job=$!

    dir="$XDG_RUNTIME_DIR/dovetail"
    for _ in $(seq 1 200); do
      [ -d "$dir" ] && [ -n "$(find "$dir" -mindepth 1 -maxdepth 1)" ] && break
      sleep 0.1
    done

    sock=$(find "$dir" -mindepth 1 -maxdepth 1 -name 'nvim-*.sock' | head -n1)
    if [ -z "$sock" ]; then
      echo "FAIL: no socket appeared under $dir"
      cat nvim.log
      exit 1
    fi
    echo "--- socket at $sock"

    ask() {
      $client --server "$sock" --remote-expr "$1"
    }

    expect() {
      local what=$1 want=$2 have
      have=$(ask "$what")
      if [ "$have" != "$want" ]; then
        echo "FAIL: $what is '$have', expected '$want'"
        exit 1
      fi
    }

    echo "--- the instance starts on other.md"
    expect 'expand("%:t")' other.md

    echo "--- dovetail-show --socket loads the named file"
    printed=$(dovetail-show --socket "$sock" note.md)
    if [ -n "$printed" ]; then
      echo "FAIL: the happy path printed '$printed'; it should print nothing"
      exit 1
    fi
    expect 'expand("%:p")' "$PWD/note.md"
    expect 'getline(1)' '# A note'

    echo "--- a relative path is resolved against the caller's directory"
    mkdir -p sub
    cat > sub/deep.md <<'EOF'
    # Deeper
    EOF
    ( cd sub && dovetail-show --socket "$sock" deep.md )
    expect 'expand("%:p")' "$PWD/sub/deep.md"

    echo "--- --line puts the cursor on the requested line"
    dovetail-show --socket "$sock" --line 4 note.md
    expect 'expand("%:p")' "$PWD/note.md"
    expect 'line(".")' 4

    echo "--- --print-socket prints the socket it used, and nothing else"
    printed=$(dovetail-show --socket "$sock" --print-socket note.md)
    if [ "$printed" != "$sock" ]; then
      echo "FAIL: --print-socket printed '$printed', expected '$sock'"
      exit 1
    fi

    echo "--- \$DOVETAIL_SOCKET is honoured like --socket"
    DOVETAIL_SOCKET="$sock" dovetail-show --line 5 note.md
    expect 'line(".")' 5

    echo "--- a socket that does not answer fails loudly and names itself"
    dead="$dir/nvim-999999.sock"
    set +e
    stderr=$(dovetail-show --socket "$dead" note.md 2>&1 >/dev/null)
    status=$?
    set -e
    if [ "$status" = "0" ]; then
      echo "FAIL: a dead socket was accepted"
      exit 1
    fi
    case "$stderr" in
      *"$dead"*) ;;
      *)
        echo "FAIL: the diagnostic does not name the socket: $stderr"
        exit 1
        ;;
    esac
    echo "--- and it did not silently open the file somewhere else"
    expect 'line(".")' 5

    echo "--- clean exit"
    $client --server "$sock" --remote-send '<C-\><C-N>:qall!<CR>' || true
    for _ in $(seq 1 200); do
      kill -0 "$nvim_job" 2>/dev/null || break
      sleep 0.1
    done
    kill -9 "$nvim_job" 2>/dev/null || true
    wait "$nvim_job" || true

    echo "--- nvim.log (should be quiet)"
    cat nvim.log

    touch $out
  ''
