# The run verb's launch path and its refusals, for the case a Nix
# sandbox actually is: no compositor at all, so the spawned terminal's
# own liveness is the only signal there is.
#
# Three things are asserted:
#
#   1. a terminal command that exits nonzero (`--terminal false`) fails
#      the whole invocation, naming both the command and its exit
#      status, rather than leaving the caller believing a resident is
#      looking at a prompt;
#   2. a terminal command that exits 0 (`--terminal true`, standing in
#      for a terminal that hands off to an already-running server) is
#      treated as fine, exactly as it is for `dovetail-show`;
#   3. every refusal — a control character in the command, in `--from`
#      or in `--why`, an empty command, and an unset terminal — exits
#      nonzero *before anything is spawned at all*. That last part is
#      what the marker file is for: a stand-in terminal that records
#      having been started, so "nothing was spawned" is checked rather
#      than assumed.
{
  runCommand,
  dovetail-run,
}:

runCommand "dovetail-run-launch-failure"
  {
    nativeBuildInputs = [ dovetail-run ];
    meta.description = "A terminal that dies fails the run loudly, and a refusal spawns nothing";
  }
  ''
    set -euo pipefail

    export HOME="$PWD/home"
    export XDG_RUNTIME_DIR="$PWD/run"
    mkdir -p "$HOME" "$XDG_RUNTIME_DIR"
    chmod 700 "$XDG_RUNTIME_DIR"

    unset SWAYSOCK DOVETAIL_TERMINAL TERMINAL || true

    marker="$PWD/spawned.marker"
    cat > record-terminal <<EOF
    #!/bin/sh
    touch "$marker"
    EOF
    chmod +x record-terminal
    recorder="$PWD/record-terminal"

    echo "--- a terminal that exits nonzero fails the invocation"
    set +e
    stderr=$(dovetail-run --terminal false "echo hi" 2>&1 >/dev/null)
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

    echo "--- a terminal that exits 0 (a daemonising terminal) is not a failure"
    dovetail-run --terminal true "echo hi"

    echo "--- the stand-in terminal is started for a command that is accepted"
    dovetail-run --terminal "$recorder" "echo hi"
    if [ ! -e "$marker" ]; then
      echo "FAIL: an accepted command did not start the terminal at all"
      exit 1
    fi

    refuses() {
      what=$1
      shift
      rm -f "$marker"
      set +e
      stderr=$(dovetail-run --terminal "$recorder" "$@" 2>&1 >/dev/null)
      status=$?
      set -e
      if [ "$status" = "0" ]; then
        echo "FAIL: $what was accepted"
        exit 1
      fi
      if [ -e "$marker" ]; then
        echo "FAIL: $what spawned a terminal before refusing"
        exit 1
      fi
      echo "--- $what: $(printf '%s' "$stderr" | head -1)"
    }

    echo "--- everything refusable is refused before anything is spawned"
    refuses "a tab in the command" "$(printf 'echo\thi')"
    refuses "a newline in the command" "$(printf 'echo hi\nrm -rf /')"
    refuses "an escape sequence in the command" "$(printf 'echo \033[2Khi')"
    refuses "a right-to-left override in the command" "echo ‮hi"
    refuses "an empty command" ""
    refuses "a newline in --from" "echo hi" --from "$(printf 'a\nseat')"
    refuses "an escape sequence in --why" "echo hi" --why "$(printf 'because \033[1m')"

    echo "--- an unset terminal is refused before anything is spawned"
    set +e
    stderr=$(dovetail-run "echo hi" 2>&1 >/dev/null)
    status=$?
    set -e
    if [ "$status" = "0" ]; then
      echo "FAIL: an unset terminal was accepted"
      exit 1
    fi
    case "$stderr" in
      *"no terminal is configured"*) ;;
      *)
        echo "FAIL: the refusal does not say the terminal is unset: $stderr"
        exit 1
        ;;
    esac

    touch $out
  ''
