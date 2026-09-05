# The scriptorium verb end to end, for the path a Nix sandbox can reach.
#
# There is no Wayland session here, so there is no layout to check: the
# two-tile arrangement is the first item on the human checklist at the
# end of `docs/scriptorium.md`. Everything else about the room is real
# and is checked here — a real editor holding the real scratch file,
# asked over RPC which file it has open:
#
#   1. the scratch file is created, under the directory the caller
#      named, with the documented `<YYYY-MM-DD>-<topic>.md` name;
#   2. stdout is exactly two lines, `socket <path>` and `file <path>`,
#      and both are true — the socket answers and the editor listening
#      on it has that file loaded;
#   3. reopening the same topic leaves an existing file byte-identical,
#      which is the whole point of a durable scratch file;
#   4. a topic that is not a slug is refused before anything is started.
#
# The terminal slot is filled with `env`, which runs its arguments and
# nothing else, and the editor slot with a wrapper that adds
# `--headless`. That is the smallest pair that produces a real Dovetail
# instance with a real socket where there is no terminal emulator and no
# display, and it exercises the same code path a resident's `foot -e`
# takes.
{
  lib,
  runCommand,
  neovim-unwrapped,
  dovetail-nvim,
  dovetail-scriptorium,
}:

runCommand "dovetail-scriptorium-room"
  {
    nativeBuildInputs = [
      dovetail-nvim
      dovetail-scriptorium
    ];
    meta.description = "dovetail-scriptorium opens the scratch file in a reachable instance";
  }
  ''
    set -euo pipefail

    client="${lib.getExe' neovim-unwrapped "nvim"} --clean --headless"

    export HOME="$PWD/home"
    export XDG_RUNTIME_DIR="$PWD/run"
    mkdir -p "$HOME" "$XDG_RUNTIME_DIR"
    chmod 700 "$XDG_RUNTIME_DIR"

    unset DOVETAIL_SCRATCH_DIR DOVETAIL_TERMINAL TERMINAL SWAYSOCK XDG_DATA_HOME || true

    # The editor slot, filled with a headless build of this flake's own
    # editor: there is no display here, and $DOVETAIL_EDITOR is exactly
    # the runtime override a resident uses for her own build.
    cat > headless-editor <<'EOF'
    #!/bin/sh
    exec nvim --headless "$@"
    EOF
    chmod +x headless-editor
    export DOVETAIL_EDITOR="$PWD/headless-editor"

    # The REPL slot is left at its build-time default on purpose: the
    # baked `python3` running under `env` with no tty exits 0 at once,
    # which is the documented daemonising-terminal case, and proves the
    # default is a real store path rather than an unsubstituted
    # placeholder.
    scratch="$PWD/scratch"

    echo "--- building a room"
    dovetail-scriptorium --terminal env --scratch-dir "$scratch" \
      parser-rewrite > room.out 2> room.err || {
        echo "FAIL: the verb exited nonzero"
        cat room.out room.err
        exit 1
      }
    cat room.err

    echo "--- stdout is exactly two labelled lines"
    if [ "$(wc -l < room.out)" != "2" ]; then
      echo "FAIL: expected two lines on stdout, got:"
      cat room.out
      exit 1
    fi

    sock=$(sed -n '1s/^socket //p' room.out)
    file=$(sed -n '2s/^file //p' room.out)
    if [ -z "$sock" ] || [ -z "$file" ]; then
      echo "FAIL: stdout is not 'socket <path>' then 'file <path>':"
      cat room.out
      exit 1
    fi
    echo "--- socket $sock"
    echo "--- file $file"

    echo "--- the file is where the convention says, with the name it says"
    want="$scratch/$(date +%F)-parser-rewrite.md"
    if [ "$file" != "$want" ]; then
      echo "FAIL: the file line says '$file', expected '$want'"
      exit 1
    fi
    if [ ! -f "$file" ]; then
      echo "FAIL: $file was reported but does not exist"
      exit 1
    fi
    if [ -s "$file" ]; then
      echo "FAIL: a new scratch file should be empty; Dovetail writes no lines into it"
      exit 1
    fi

    ask() {
      $client --server "$sock" --remote-expr "$1"
    }

    echo "--- the socket answers, and the scratch file is what it has open"
    if [ "$(ask '1 + 1')" != "2" ]; then
      echo "FAIL: the printed socket does not answer"
      exit 1
    fi
    have=$(ask 'expand("%:p")')
    if [ "$have" != "$file" ]; then
      echo "FAIL: the instance has '$have' open, not the scratch file"
      exit 1
    fi

    echo "--- the resident writes something and it is hers"
    $client --server "$sock" --remote-send \
      '<C-\><C-N>ggIThe first line is the resident'"'"'s.<Esc>:w<CR>'
    for _ in $(seq 1 100); do
      [ -s "$file" ] && break
      sleep 0.1
    done
    before=$(sha256sum < "$file")
    $client --server "$sock" --remote-send '<C-\><C-N>:qall!<CR>' || true

    echo "--- reopening the same topic never truncates"
    dovetail-scriptorium --terminal env --scratch-dir "$scratch" \
      parser-rewrite > reopen.out 2> reopen.err
    cat reopen.err
    reopened=$(sed -n '2s/^file //p' reopen.out)
    if [ "$reopened" != "$file" ]; then
      echo "FAIL: reopening named a different file: '$reopened'"
      exit 1
    fi
    after=$(sha256sum < "$file")
    if [ "$before" != "$after" ]; then
      echo "FAIL: reopening changed the file"
      exit 1
    fi
    resock=$(sed -n '1s/^socket //p' reopen.out)
    if [ "$($client --server "$resock" --remote-expr 'getline(1)')" \
         != "The first line is the resident's." ]; then
      echo "FAIL: the reopened buffer is not yesterday's content"
      exit 1
    fi
    $client --server "$resock" --remote-send '<C-\><C-N>:qall!<CR>' || true

    echo "--- a topic that is not a slug is refused before anything starts"
    set +e
    stderr=$(dovetail-scriptorium --terminal env --scratch-dir "$scratch" \
      "Parser Rewrite" 2>&1 >/dev/null)
    status=$?
    set -e
    if [ "$status" = "0" ]; then
      echo "FAIL: a topic that is not a slug was accepted"
      exit 1
    fi
    case "$stderr" in
      *"parser-rewrite"*) ;;
      *)
        echo "FAIL: the refusal does not suggest what was meant: $stderr"
        exit 1
        ;;
    esac
    if [ "$(find "$scratch" -maxdepth 1 -type f | wc -l)" != "1" ]; then
      echo "FAIL: the refusal left files behind:"
      find "$scratch" -maxdepth 1 -type f
      exit 1
    fi

    echo "--- the scratch directory is private"
    mode=$(stat -c %a "$scratch")
    if [ "$mode" != "700" ]; then
      echo "FAIL: the scratch directory is mode $mode, expected 700"
      exit 1
    fi

    touch $out
  ''
