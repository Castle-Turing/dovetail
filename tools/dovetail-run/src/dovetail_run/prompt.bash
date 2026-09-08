# The prompt the resident is handed. Run by `dovetail-run` as the
# trailing arguments of the terminal the resident named, with either
# five arguments or seven: the provenance block to print, the command to
# pre-fill, a path to record the interaction's outcome to (empty means
# don't), and the raw `--from`/`--why` text the record wants verbatim
# (also empty when neither was given) are always present. The recorder
# binary and the transcript path it writes to trail those five only when
# `--record` was given — a fixed-arity pair, present together or not at
# all, never as two more empty strings. All seven, when present, have
# already been refused-or-passed by `sanitize.py`, so nothing here has
# to defend against a newline or an escape sequence.
#
# It is not executable and has no shebang: the verb names bash by store
# path and hands this file to it, so the shell that runs the prompt is
# the one the package was built with rather than whatever `env` finds.
#
# The one rule this file exists to keep is that the line the resident
# reads is the line that runs. So it does nothing to that line: no
# expansion before it is displayed, no rewriting after it is accepted,
# and no default answer. `read -e` is a real readline line — arrow keys,
# word motions, kill and yank all work — and `-i` seeds it with the
# proposal rather than typing it for her.

if [ "$#" -ne 5 ] && [ "$#" -ne 7 ]; then
    printf 'dovetail-run: the prompt wrapper takes five or seven arguments, got %d\n' "$#" >&2
    exit 2
fi

provenance=$1
proposal=$2
record_path=$3
record_from=$4
record_why=$5
recorder=${6-}
transcript_path=${7-}

# The record needs a JSON encoder, which bash does not have, so writing
# it is delegated to a standalone script shipped beside this one — found
# by our own path (`$0`, pure parameter expansion, no `dirname` process)
# rather than baked in, because it lives in the same directory this file
# does no matter where the package is installed. The interpreter that
# runs it *is* baked in, the same reasoning as bash itself: the
# resident's terminal may put no Python, or a different one, on its
# `$PATH`.
python_bin='@dovetailPython@'
case "$python_bin" in
    @*) python_bin=python3 ;;
esac
record_writer="${0%/*}/record.py"

# Writes the record if and only if `--record` was given; a no-op
# otherwise. Never touches `status`: a record that fails to write is a
# warning on stderr, not a reason to change what this window reports
# about the command itself.
#   $1 declined ("true"/"false")  $2 executed line  $3 exit status
#   $4 transcript path (empty when declined — nothing was captured)
write_record() {
    [ -n "$record_path" ] || return 0
    # A declined record claims no transcript. If this record path was
    # used before and did produce one, it is still sitting beside it —
    # `script` only ever overwrites that file on an *accepted* line —
    # and would otherwise outlive the record that now says nothing was
    # captured, making stale output look like it belongs to this run.
    if [ "$1" = "true" ] && [ -n "$transcript_path" ]; then
        rm -f -- "$transcript_path"
    fi
    local finished_at
    TZ=UTC printf -v finished_at '%(%Y-%m-%dT%H:%M:%SZ)T' -1
    if ! "$python_bin" "$record_writer" \
        "$record_path" "$1" "$proposal" "$2" "$3" "$4" \
        "$record_from" "$record_why" "$proposed_at" "$finished_at"; then
        printf 'dovetail-run: could not write the record to %s\n' "$record_path" >&2
    fi
}

if [ -n "$record_path" ]; then
    TZ=UTC printf -v proposed_at '%(%Y-%m-%dT%H:%M:%SZ)T' -1
fi

# Nothing is written to any history file. The resident's shell history
# belongs to the resident's shell, and a one-shot prompt appending to it
# uninvited would put a command she may never have run into the record
# she greps. `read -e` does not add to the history list on its own; this
# makes sure nothing else can either.
unset HISTFILE
set +o history

# No terminal means the line cannot be displayed, and a line that cannot
# be displayed must not run: the whole promise is that she read it. This
# is the case where a terminal argv prefix runs its argument without a
# tty — refuse rather than quietly reading the proposal from a pipe.
if [ ! -t 0 ]; then
    printf 'dovetail-run: no terminal on standard input, so the command cannot be shown; nothing was run\n' >&2
    exit 2
fi

printf '%s\n\n' "$provenance"

# `-r` so a backslash in the proposal survives as a backslash. IFS
# emptied so leading and trailing spaces are not eaten: what is
# displayed is what runs, byte for byte, and trimming would be a repair.
if ! IFS= read -e -r -i "$proposal" -p '$ ' line; then
    printf '\ndovetail-run: end of input; nothing was run.\n'
    write_record true "" "" ""
    exit 0
fi

if [ -z "${line//[[:space:]]/}" ]; then
    printf 'dovetail-run: the line was cleared; nothing was run.\n'
    write_record true "" "" ""
    exit 0
fi

# Under --record, the accepted line runs inside `script` instead of a
# bare `eval`, so what the resident sees is captured to a transcript
# while she still sees it as a real terminal — progress bars, prompts
# and color survive. $BASH is bash's own built-in for the exact path
# used to invoke this instance, so SHELL names the very same bash the
# rest of this file runs under: a command written for bash's syntax is
# still run by bash, recorder or not. `-e` hands back the command's own
# exit status rather than script's; `-q` only quiets script's own
# start/done banner on screen, not in the transcript file, which still
# opens and closes with it. The `--` stops a transcript path that
# happens to start with `-` from being parsed as another option.
#
# `script` can fail before `$line` ever starts — its destination
# already a directory, unwritable, or gone missing underneath it — and
# then its own exit status is not the command's. The stale file is
# cleared first so that success is the only way the path ends this
# block holding a real transcript: if it does not, `script` never got
# as far as running anything, and the line that was accepted must not
# be reported as though it had.
if [ -n "$transcript_path" ]; then
    rm -f -- "$transcript_path"
    SHELL="$BASH" "$recorder" -qec "$line" -- "$transcript_path"
    status=$?
    if [ ! -f "$transcript_path" ]; then
        printf 'dovetail-run: the recorder could not open the transcript at %s; nothing was run\n' "$transcript_path" >&2
        write_record true "" "" ""
        exit 1
    fi
else
    eval "$line"
    status=$?
fi

# Written now, not after the hold-open read below: a caller polling for
# the record is waiting on the correction signal, not on the resident
# having read the output and closed the window. The transcript is
# already complete by this point too — `script` above has already
# exited — so a poller that waits for this record never reads a partial
# transcript.
write_record false "$line" "$status" "$transcript_path"

# The window belongs to the resident until she is finished reading it.
# A terminal that closes on the command's last line of output is a
# command whose output nobody saw.
printf '\ndovetail-run: exit status %d. Press Enter to close this window.' "$status"
read -r _ || true
exit "$status"
