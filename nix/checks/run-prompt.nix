# The prompt itself, driven under a pseudo-terminal.
#
# This is the one claim `dovetail-run` makes — the line the resident
# reads is the line that runs, and nothing runs until she presses
# Enter — checked against a real bash rather than asserted in prose.
# `read -e -i` is verified here, under a pty, because that is the only
# place it can be: it needs a terminal, and a terminal is exactly what a
# Nix sandbox does not hand a build.
#
# So the terminal slot is filled with a pty-allocating stand-in. It runs
# its arguments under a pty the way `foot -e` runs them under a real
# one, types a prepared key sequence at the prompt, and writes down
# every byte the prompt drew. The whole argv path is exercised: the
# terminal prefix the resident names, the bash the package baked in, the
# wrapper shipped inside it, and the two sanitized strings.
#
# Four cases, and each proves its claim by side effect rather than by
# reading the transcript for encouraging words:
#
#   1. Enter on the pre-filled line runs exactly the proposed command,
#      and the line drawn on screen is byte-equal to what was proposed;
#   2. an edited line runs the edited line, and the line drawn is
#      byte-equal to the edit;
#   3. a cleared line runs nothing and says it declined;
#   4. a terminal that gives the prompt no tty runs nothing and fails
#      the invocation, because a line that cannot be displayed must not
#      run.
{
  runCommand,
  python3,
  dovetail-run,
}:

runCommand "dovetail-run-prompt"
  {
    nativeBuildInputs = [
      dovetail-run
      python3
    ];
    meta.description = "The pre-filled prompt runs what it displays, and only when Enter is pressed";
  }
  ''
    set -euo pipefail

    export HOME="$PWD/home"
    export XDG_RUNTIME_DIR="$PWD/run"
    mkdir -p "$HOME" "$XDG_RUNTIME_DIR"
    chmod 700 "$XDG_RUNTIME_DIR"

    # No compositor: the verb takes its no-compositor branch, watches
    # the stand-in terminal for a couple of seconds, and returns while
    # the prompt is still up.
    unset SWAYSOCK DOVETAIL_TERMINAL TERMINAL || true

    # readline is what is being tested, so it gets a terminal type it
    # knows rather than the empty $TERM a Nix build starts with.
    export TERM=xterm

    cp ${./run-prompt-terminal.py} pty-terminal.py
    cp ${./run-prompt-assert.py} assert.py

    terminal="python3 $PWD/pty-terminal.py"

    # $PTY_KEYS is what the resident types once the prompt is drawn,
    # and $PTY_CAPTURE is where every byte the prompt drew is written.
    # Both reach the stand-in through the environment the verb spawns
    # it with.
    propose() {
      capture=$1
      keys=$2
      shift 2
      PTY_CAPTURE="$PWD/$capture" PTY_KEYS="$keys" \
        dovetail-run --terminal "$terminal" \
          --from "the run-prompt check" \
          --why "proving that what is displayed is what runs" \
          "$@"
      for _ in $(seq 1 300); do
        [ -f "$PWD/$capture" ] && return 0
        sleep 0.1
      done
      echo "FAIL: the prompt never finished; no capture at $PWD/$capture"
      exit 1
    }

    echo "--- Enter on the pre-filled line runs exactly the proposed command"
    enter_command="printf %s ENTER-RAN > $PWD/enter.txt"
    propose enter.cap '\r' "$enter_command"
    if [ "$(cat enter.txt)" != "ENTER-RAN" ]; then
      echo "FAIL: the proposed command did not run; enter.txt is:"
      cat enter.txt || true
      exit 1
    fi
    python3 assert.py enter.cap "$enter_command"
    grep -q "the run-prompt check" enter.cap || {
      echo "FAIL: the provenance block did not name the proposer"
      exit 1
    }
    grep -q "proving that what is displayed is what runs" enter.cap || {
      echo "FAIL: the provenance block did not give the reason"
      exit 1
    }

    echo "--- an edited line runs the edited line"
    edit_command="printf %s EDIT > $PWD/edit.txt"
    edit_suffix=" ; printf %s -MORE >> $PWD/edit.txt"
    propose edit.cap "$edit_suffix"'\r' "$edit_command"
    if [ "$(cat edit.txt)" != "EDIT-MORE" ]; then
      echo "FAIL: the edited line did not run; edit.txt is:"
      cat edit.txt || true
      exit 1
    fi
    python3 assert.py edit.cap "$edit_command$edit_suffix"

    echo "--- a cleared line runs nothing and says it declined"
    # \x15 is Ctrl-U, which readline binds to unix-line-discard.
    propose decline.cap '\x15\r' "printf %s DECLINED > $PWD/declined.txt"
    if [ -e declined.txt ]; then
      echo "FAIL: a declined command ran anyway"
      exit 1
    fi
    grep -q "the line was cleared; nothing was run" decline.cap || {
      echo "FAIL: the decline was not reported; the capture is:"
      cat decline.cap
      exit 1
    }

    echo "--- a terminal with no tty shows nothing, so it runs nothing"
    set +e
    stderr=$(dovetail-run --terminal env "printf %s NOTTY > $PWD/notty.txt" 2>&1 >/dev/null)
    status=$?
    set -e
    if [ "$status" = "0" ]; then
      echo "FAIL: a prompt that could not be displayed was reported as success"
      exit 1
    fi
    if [ -e notty.txt ]; then
      echo "FAIL: a command ran without being displayed to anyone"
      exit 1
    fi
    case "$stderr" in
      *"status 2"*) ;;
      *)
        echo "FAIL: the diagnostic does not name the exit status: $stderr"
        exit 1
        ;;
    esac
    echo "--- diagnostic: $stderr"

    touch $out
  ''
