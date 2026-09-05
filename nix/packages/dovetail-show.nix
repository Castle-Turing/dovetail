# `dovetail-show`, the show verb, as a package.
#
# Two absolute store paths are baked in here, and they are the only
# build-time configuration the tool has:
#
#   the editor to launch when nothing overrides it — this flake's own
#   `dovetail` package, overridable at runtime with $DOVETAIL_EDITOR;
#
#   the client used to talk to a running instance — plain unwrapped
#   Neovim, so the tool never depends on the configuration whose files
#   it is opening.
#
# `swaymsg` is deliberately *not* baked in and not added to the closure.
# It belongs to the resident's running compositor, is found on $PATH,
# and its absence is an ordinary answer — "no focused editor" — rather
# than an error.
{
  lib,
  python3Packages,
  neovim-unwrapped,
  dovetail-nvim,
}:

python3Packages.buildPythonApplication {
  pname = "dovetail-show";
  version = "0.1.0";
  pyproject = true;

  src = ../../tools/dovetail-show;

  build-system = [ python3Packages.setuptools ];

  postPatch = ''
    substituteInPlace src/dovetail_show/defaults.py \
      --replace-fail '@dovetailEditor@' '${lib.getExe' dovetail-nvim "nvim"}' \
      --replace-fail '@dovetailNvimClient@' '${lib.getExe' neovim-unwrapped "nvim"}'
  '';

  # The unit tests over the targeting rule run as part of building the
  # package, so `nix flake check` gets them by depending on this output.
  nativeCheckInputs = [ python3Packages.pytestCheckHook ];

  pythonImportsCheck = [ "dovetail_show" ];

  meta = {
    description = "Open a file in the focused Dovetail editor, or in a new floating one";
    mainProgram = "dovetail-show";
    license = lib.licenses.mit;
    platforms = lib.platforms.unix;
  };
}
