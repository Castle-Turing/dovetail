# The reachability check, run by `nix flake check`.
#
# It asserts the whole of the socket path scheme from the outside, the
# way a consumer will meet it:
#
#   1. a headless instance creates exactly one socket under
#      $XDG_RUNTIME_DIR/dovetail, named nvim-<pid>.sock;
#   2. the <pid> in the name is the instance's own, confirmed by asking
#      the instance over the socket rather than by trusting the shell;
#   3. a trivial expression round-trips over msgpack-RPC;
#   4. the markdown prose defaults are set buffer-locally, and the
#      markdown treesitter parser is on the runtime path;
#   5. a clean exit removes the socket and leaves the directory empty.
#
# The RPC client is plain unwrapped Neovim (`--server ... --remote-expr`),
# so the check depends on nothing Dovetail ships and cannot accidentally
# pass by talking to itself.
{
  lib,
  runCommand,
  neovim-unwrapped,
  dovetail-nvim,
}:

runCommand "dovetail-headless-socket"
  {
    nativeBuildInputs = [ dovetail-nvim ];
    meta.description = "Dovetail instances are born reachable at the documented socket path";
  }
  ''
    set -euo pipefail

    client="${lib.getExe' neovim-unwrapped "nvim"} --clean --headless"

    export HOME="$PWD/home"
    export XDG_RUNTIME_DIR="$PWD/run"
    mkdir -p "$HOME" "$XDG_RUNTIME_DIR"
    chmod 700 "$XDG_RUNTIME_DIR"

    cat > note.md <<'EOF'
    # A note

    One long paragraph of prose, so that the wrap settings have something
    to act on when a human eventually looks at this by hand.
    EOF

    echo "--- launching a headless instance"
    nvim --headless note.md </dev/null >nvim.log 2>&1 &
    nvim_job=$!

    dir="$XDG_RUNTIME_DIR/dovetail"

    entries() {
      if [ -d "$dir" ]; then
        find "$dir" -mindepth 1 -maxdepth 1 | sort
      fi
    }

    for _ in $(seq 1 200); do
      [ -n "$(entries)" ] && break
      sleep 0.1
    done

    sockets=$(entries)
    count=$(printf '%s\n' "$sockets" | grep -c . || true)
    if [ "$count" != "1" ]; then
      echo "FAIL: expected exactly one entry under $dir, found $count:"
      printf '%s\n' "$sockets"
      echo "--- nvim.log"
      cat nvim.log
      exit 1
    fi

    sock="$sockets"
    if [ ! -S "$sock" ]; then
      echo "FAIL: $sock exists but is not a socket"
      exit 1
    fi

    name_pid=$(basename "$sock" .sock)
    name_pid=''${name_pid#nvim-}
    case "$name_pid" in
      "" | *[!0-9]*)
        echo "FAIL: $sock does not match the nvim-<pid>.sock scheme"
        exit 1
        ;;
    esac
    echo "--- socket at $sock"

    ask() {
      $client --server "$sock" --remote-expr "$1"
    }

    echo "--- RPC round-trip"
    got=$(ask '1 + 1')
    if [ "$got" != "2" ]; then
      echo "FAIL: expected 2 over RPC, got '$got'"
      exit 1
    fi

    echo "--- the pid in the socket name is this instance's own"
    got=$(ask 'getpid()')
    if [ "$got" != "$name_pid" ]; then
      echo "FAIL: socket is named for pid $name_pid but the instance reports $got"
      exit 1
    fi

    echo "--- the instance agrees on its own socket path"
    got=$(ask 'get(g:, "dovetail_socket", "<unset>")')
    if [ "$got" != "$sock" ]; then
      echo "FAIL: g:dovetail_socket is '$got', expected '$sock'"
      exit 1
    fi
    got=$(ask 'get(g:, "dovetail_socket_error", "")')
    if [ -n "$got" ]; then
      echo "FAIL: g:dovetail_socket_error is set: $got"
      exit 1
    fi

    echo "--- markdown prose defaults are buffer-local"
    expect_buf_opt() {
      local option=$1 want=$2
      local have
      have=$(ask "getbufvar(1, '&$option')")
      if [ "$have" != "$want" ]; then
        echo "FAIL: markdown buffer has &$option = '$have', expected '$want'"
        exit 1
      fi
    }
    expect_buf_opt filetype markdown
    expect_buf_opt wrap 1
    expect_buf_opt linebreak 1
    expect_buf_opt breakindent 1
    expect_buf_opt textwidth 0

    echo "--- and they really are buffer-local, not global"
    got=$(ask '&g:linebreak')
    if [ "$got" != "0" ]; then
      echo "FAIL: linebreak leaked into the global option (got '$got', expected 0)"
      exit 1
    fi

    echo "--- the markdown treesitter parser is on the runtime path"
    got=$(ask 'len(nvim_get_runtime_file("parser/markdown.so", v:false))')
    if [ "$got" = "0" ]; then
      echo "FAIL: no markdown treesitter parser found on the runtime path"
      exit 1
    fi

    echo "--- clean exit"
    $client --server "$sock" --remote-send '<C-\><C-N>:qall!<CR>' || true

    for _ in $(seq 1 200); do
      kill -0 "$nvim_job" 2>/dev/null || break
      sleep 0.1
    done
    if kill -0 "$nvim_job" 2>/dev/null; then
      echo "FAIL: the instance did not exit after :qall!"
      kill -9 "$nvim_job" || true
      exit 1
    fi
    wait "$nvim_job" || true

    if [ -e "$sock" ]; then
      echo "FAIL: $sock survived a clean exit"
      exit 1
    fi
    leftovers=$(entries)
    if [ -n "$leftovers" ]; then
      echo "FAIL: $dir is not empty after a clean exit:"
      printf '%s\n' "$leftovers"
      exit 1
    fi

    echo "--- nvim.log (should be quiet)"
    cat nvim.log

    touch $out
  ''
