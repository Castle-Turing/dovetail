# The launch path's failure detection, for the one launch case a sandbox
# can reach: no compositor at all. `swaymsg` is not on the closure and
# `$SWAYSOCK` is unset, so this is exactly the "no reachable compositor"
# branch of `launch.py` — the one that used to have no diagnostic at all
# when the spawned terminal died instead of opening anything.
#
# Two things are asserted:
#
#   1. a terminal command that exits immediately with a nonzero status
#      (`--terminal false`) fails the whole invocation, naming both the
#      command and its exit status, rather than reporting success;
#   2. a terminal command that exits immediately with status 0 (`--terminal
#      true`) is treated as fine, the same as a terminal that daemonizes
#      and hands off to an already-running server — so the new liveness
#      watch does not turn every quick, successful exit into a failure.
{
  runCommand,
  dovetail-show,
}:

runCommand "dovetail-show-launch-failure"
  {
    nativeBuildInputs = [ dovetail-show ];
    meta.description = "A terminal that dies without a compositor fails the launch, loudly";
  }
  ''
    set -euo pipefail

    export HOME="$PWD/home"
    export XDG_RUNTIME_DIR="$PWD/run"
    mkdir -p "$HOME" "$XDG_RUNTIME_DIR"
    chmod 700 "$XDG_RUNTIME_DIR"

    # No compositor reachable, and no other instance to fall back to.
    unset SWAYSOCK DOVETAIL_SOCKET || true

    echo "# Not shown" > note.md

    echo "--- a terminal that exits nonzero fails the invocation"
    set +e
    stderr=$(dovetail-show --terminal false note.md 2>&1 >/dev/null)
    status=$?
    set -e
    if [ "$status" = "0" ]; then
      echo "FAIL: a terminal that exited nonzero was reported as success"
      exit 1
    fi
    case "$stderr" in
      *"false"*"status 1"*) ;;
      *)
        echo "FAIL: the diagnostic does not name the command and its status: $stderr"
        exit 1
        ;;
    esac
    echo "--- diagnostic: $stderr"

    echo "--- a terminal that exits 0 (a daemonizing terminal) is not a failure"
    dovetail-show --terminal true note.md

    touch $out
  ''
