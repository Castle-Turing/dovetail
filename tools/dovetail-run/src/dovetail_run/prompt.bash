# The prompt the resident is handed. Run by `dovetail-run` as the
# trailing arguments of the terminal the resident named, with exactly
# five arguments: the provenance block to print, the command to
# pre-fill, a path to record the interaction's outcome to (empty means
# don't), and the raw `--from`/`--why` text the record wants verbatim
# (also empty when neither was given). All five have already been
# refused-or-passed by `sanitize.py`, so nothing here has to defend
# against a newline or an escape sequence.
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

if [ "$#" -ne 5 ]; then
    printf 'dovetail-run: the prompt wrapper takes five arguments, got %d\n' "$#" >&2
    exit 2
fi

provenance=$1
proposal=$2
record_path=$3
record_from=$4
record_why=$5

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
write_record() {
    [ -n "$record_path" ] || return 0
    local finished_at
    TZ=UTC printf -v finished_at '%(%Y-%m-%dT%H:%M:%SZ)T' -1
    if ! "$python_bin" "$record_writer" \
        "$record_path" "$1" "$proposal" "$2" "$3" \
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
    write_record true "" ""
    exit 0
fi

if [ -z "${line//[[:space:]]/}" ]; then
    printf 'dovetail-run: the line was cleared; nothing was run.\n'
    write_record true "" ""
    exit 0
fi

eval "$line"
status=$?

# Written now, not after the hold-open read below: a caller polling for
# the record is waiting on the correction signal, not on the resident
# having read the output and closed the window.
write_record false "$line" "$status"

# The window belongs to the resident until she is finished reading it.
# A terminal that closes on the command's last line of output is a
# command whose output nobody saw.
printf '\ndovetail-run: exit status %d. Press Enter to close this window.' "$status"
read -r _ || true
exit "$status"
