# `dovetail-scriptorium`, the scriptorium verb, as a package.
#
# Everything it needs beyond its own scratch file convention and layout
# rule — the compositor seam, the editor seam, the launch machinery, and
# the store paths baked into them, including the `python3` it runs as the
# default REPL — comes from `dovetail-seams`.
{
  lib,
  python3Packages,
  dovetail-seams,
}:

python3Packages.buildPythonApplication {
  pname = "dovetail-scriptorium";
  version = "0.1.0";
  pyproject = true;

  src = ../../tools/dovetail-scriptorium;

  build-system = [ python3Packages.setuptools ];

  dependencies = [ dovetail-seams ];

  # The unit tests over the scratch file convention, the layout rule and
  # the order the steps run in all run as part of building the package,
  # so `nix flake check` gets them by depending on this output.
  nativeCheckInputs = [ python3Packages.pytestCheckHook ];

  pythonImportsCheck = [ "dovetail_scriptorium" ];

  meta = {
    description = "Build a worksession: a scratch file in an editor tile, a REPL beside it";
    mainProgram = "dovetail-scriptorium";
    license = lib.licenses.mit;
    platforms = lib.platforms.unix;
  };
}
