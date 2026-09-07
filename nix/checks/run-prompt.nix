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
#
# Task 0010 adds `--record`, checked against the same three interactive
# cases: the accepted line's record has `proposed == executed`, the
# edited line's record has `proposed != executed`, and the declined
# case's record has `executed` and `exit_status` both null. A fourth
# record check is negative — a proposal with no `--record` at all
# writes no file — and a final one is over every record written by this
# check: no temporary file from the atomic-rename step is left behind,
# which is what "never a half-written record" comes down to on disk.
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
    cp ${./run-record-assert.py} record-assert.py

    terminal="python3 $PWD/pty-terminal.py"

    assert_record() {
      python3 record-assert.py "$@"
    }

    # $PTY_KEYS is what the resident types once the prompt is drawn,
    # and $PTY_CAPTURE is where every byte the prompt drew is written.
    # Both reach the stand-in through the environment the verb spawns
    # it with. $3, when given, is a --record path: the record is
    # written before the wrapper's final hold-open read, so waiting for
    # the capture file — written only once the whole process has
    # exited — is waiting long enough for the record file too.
    propose() {
      capture=$1
      keys=$2
      record=$3
      shift 3
      extra_args=()
      if [ -n "$record" ]; then
        extra_args=(--record "$record")
      fi
      PTY_CAPTURE="$PWD/$capture" PTY_KEYS="$keys" \
        dovetail-run --terminal "$terminal" \
          --from "the run-prompt check" \
          --why "proving that what is displayed is what runs" \
          "''${extra_args[@]}" \
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
    propose enter.cap '\r' "$PWD/enter.record.json" "$enter_command"
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
    if [ ! -f enter.record.json ]; then
      echo "FAIL: --record was given but enter.record.json was never written"
      exit 1
    fi
    assert_record enter.record.json proposed "$enter_command"
    assert_record enter.record.json executed "$enter_command"
    assert_record enter.record.json declined false
    assert_record enter.record.json exit_status 0
    assert_record enter.record.json from "the run-prompt check"
    assert_record enter.record.json why "proving that what is displayed is what runs"

    echo "--- an edited line runs the edited line"
    edit_command="printf %s EDIT > $PWD/edit.txt"
    edit_suffix=" ; printf %s -MORE >> $PWD/edit.txt"
    propose edit.cap "$edit_suffix"'\r' "$PWD/edit.record.json" "$edit_command"
    if [ "$(cat edit.txt)" != "EDIT-MORE" ]; then
      echo "FAIL: the edited line did not run; edit.txt is:"
      cat edit.txt || true
      exit 1
    fi
    python3 assert.py edit.cap "$edit_command$edit_suffix"
    assert_record edit.record.json proposed "$edit_command"
    assert_record edit.record.json executed "$edit_command$edit_suffix"
    assert_record edit.record.json declined false
    assert_record edit.record.json exit_status 0
    if [ "$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["proposed"] != d["executed"])' edit.record.json)" != "True" ]; then
      echo "FAIL: an edited command's record has proposed == executed"
      exit 1
    fi

    echo "--- a cleared line runs nothing and says it declined"
    # \x15 is Ctrl-U, which readline binds to unix-line-discard.
    decline_command="printf %s DECLINED > $PWD/declined.txt"
    propose decline.cap '\x15\r' "$PWD/decline.record.json" "$decline_command"
    if [ -e declined.txt ]; then
      echo "FAIL: a declined command ran anyway"
      exit 1
    fi
    grep -q "the line was cleared; nothing was run" decline.cap || {
      echo "FAIL: the decline was not reported; the capture is:"
      cat decline.cap
      exit 1
    }
    assert_record decline.record.json proposed "$decline_command"
    assert_record decline.record.json executed null
    assert_record decline.record.json declined true
    assert_record decline.record.json exit_status null

    echo "--- without --record, nothing is ever written"
    before_files=$(ls "$PWD" | sort)
    propose norecord.cap '\r' "" "printf %s NORECORD > $PWD/norecord.txt"
    if [ "$(cat norecord.txt)" != "NORECORD" ]; then
      echo "FAIL: the proposed command did not run; norecord.txt is:"
      cat norecord.txt || true
      exit 1
    fi
    after_files=$(ls "$PWD" | sort)
    new_files=$(comm -13 <(echo "$before_files") <(echo "$after_files"))
    if [ "$new_files" != "$(printf 'norecord.cap\nnorecord.txt')" ]; then
      echo "FAIL: without --record, unexpected files appeared: $new_files"
      exit 1
    fi

    echo "--- no half-written record is ever left behind"
    if find "$PWD" -maxdepth 1 -name '.*.tmp' -print -quit | grep -q .; then
      echo "FAIL: a temporary record file survived past the atomic rename:"
      find "$PWD" -maxdepth 1 -name '.*.tmp'
      exit 1
    fi

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
