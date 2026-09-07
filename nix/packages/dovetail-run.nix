# `dovetail-run`, the run verb, as a package.
#
# Everything it needs beyond its own refusals and its prompt — the
# compositor seam, the terminal slot, and the launch machinery, along
# with the store paths baked into them — comes from `dovetail-seams`.
#
# Two store paths are baked in here that no other verb needs: the bash
# that runs the prompt, and the Python that writes the record afterwards.
# The prompt is a real readline line (`read -e -i`), which is a bash
# feature, and the resident's terminal may start any shell or none at
# all — so the shell is named by absolute path rather than found on
# `$PATH`. The record needs a JSON encoder bash does not have, and the
# same terminal may put no Python, or a different one, on its `$PATH`
# either. There is no runtime override for either, because a shell or a
# Python that cannot run these scripts cannot hold the slot.
{
  lib,
  bash,
  python3,
  python3Packages,
  dovetail-seams,
}:

python3Packages.buildPythonApplication {
  pname = "dovetail-run";
  version = "0.1.0";
  pyproject = true;

  src = ../../tools/dovetail-run;

  build-system = [ python3Packages.setuptools ];

  dependencies = [ dovetail-seams ];

  postPatch = ''
    substituteInPlace src/dovetail_run/defaults.py \
      --replace-fail '@dovetailBash@' '${lib.getExe' bash "bash"}'
    substituteInPlace src/dovetail_run/prompt.bash \
      --replace-fail '@dovetailPython@' '${lib.getExe python3}'
  '';

  # The unit tests over the refusals, the provenance block and the argv
  # the terminal is handed all run as part of building the package, so
  # `nix flake check` gets them by depending on this output.
  nativeCheckInputs = [ python3Packages.pytestCheckHook ];

  pythonImportsCheck = [ "dovetail_run" ];

  meta = {
    description = "Put a command in front of the resident, pre-filled and editable, without running it";
    mainProgram = "dovetail-run";
    license = lib.licenses.mit;
    platforms = lib.platforms.unix;
  };
}
