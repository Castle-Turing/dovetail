{
  description = "Dovetail — the editor joint: a nixvim module whose every instance is born reachable over a socket";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

    # Deliberately not `inputs.nixpkgs.follows = "nixpkgs"`. Nixvim is
    # tested against the Nixpkgs it pins and warns — fatally, in its own
    # `build.test` — when that pin is overridden. So the editor is built
    # from Nixvim's Nixpkgs, and the `nixpkgs` input above supplies only
    # the scaffolding around it: the check runner, the RPC client, the
    # formatter. Having the check talk to the editor across two Nixpkgs
    # revisions is a small bonus: it proves the socket is a real
    # interface and not an artefact of one closure.
    nixvim.url = "github:nix-community/nixvim";
  };

  outputs =
    {
      self,
      nixpkgs,
      nixvim,
    }:
    let
      # x86_64-darwin is absent because Nixpkgs 26.11 dropped it.
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
      ];

      forAllSystems =
        f:
        nixpkgs.lib.genAttrs systems (
          system:
          f {
            inherit system;
            pkgs = nixpkgs.legacyPackages.${system};
          }
        );

      # Evaluate the Dovetail module, plus whatever a caller imports
      # alongside it. This is the overlay point: a private layer is just
      # another nixvim module in `modules`, with no Dovetail-specific
      # option to learn. See `docs/module.md`.
      evalDovetail =
        {
          system,
          modules ? [ ],
        }:
        nixvim.lib.evalNixvim {
          inherit system;
          modules = [ self.nixvimModules.dovetail ] ++ modules;
        };
    in
    {
      # The module, in the attribute shape nixvim's own flake declares for
      # reusable nixvim modules. Import it into any nixvim evaluation:
      # standalone via `nixvim.lib.evalNixvim`, or under `programs.nixvim`
      # in Home Manager, NixOS or nix-darwin.
      nixvimModules = {
        dovetail = ./nix/module.nix;
        default = self.nixvimModules.dovetail;
      };

      lib = {
        inherit evalDovetail;
      };

      # A runnable editor, so a stranger can `nix run github:...#dovetail`
      # without adopting any module system — and the verbs that drive it,
      # over the seams they share.
      #
      # `default` stays the editor: `nix run github:Castle-Turing/dovetail`
      # is a documented entry point in `docs/module.md` and keeps meaning
      # what that document says it means. Each verb is its own executable
      # rather than a subcommand of `dovetail`, because `dovetail` already
      # names the editor and a word doing two jobs is a defect.
      packages = forAllSystems (
        { system, pkgs }:
        rec {
          dovetail = (evalDovetail { inherit system; }).config.build.package;
          default = dovetail;

          # Not an executable: the compositor, editor, process and
          # launch seams the verbs share, and the one place the editor,
          # the RPC client and the REPL are baked in as store paths. It
          # is an output so that its unit tests are a check.
          dovetail-seams = pkgs.callPackage ./nix/packages/dovetail-seams.nix {
            dovetail-nvim = dovetail;
          };

          dovetail-show = pkgs.callPackage ./nix/packages/dovetail-show.nix {
            inherit dovetail-seams;
          };

          dovetail-scriptorium = pkgs.callPackage ./nix/packages/dovetail-scriptorium.nix {
            inherit dovetail-seams;
          };

          dovetail-run = pkgs.callPackage ./nix/packages/dovetail-run.nix {
            inherit dovetail-seams;
          };
        }
      );

      checks = forAllSystems (
        { system, pkgs }:
        {
          # Nixvim's own smoke test: the configuration evaluates without
          # warnings or assertions, and `nvim` starts and quits silently.
          config = (evalDovetail { inherit system; }).config.build.test;

          # The reachability guarantee, end to end: socket appears at the
          # documented path, answers RPC, and is gone after a clean exit.
          headless-socket = pkgs.callPackage ./nix/checks/headless-socket.nix {
            dovetail-nvim = self.packages.${system}.dovetail;
          };

          # The overlay point holds: a second module carrying nothing but
          # taste composes with ours and still builds.
          overlay-point =
            (evalDovetail {
              inherit system;
              modules = [ ./nix/checks/example-private-layer.nix ];
            }).config.build.test;

          # The unit tests over the shared seams — the slots, the
          # compositor's window wait, the process table — which run in
          # the package's own check phase, so this check is the package.
          seams-unit = self.packages.${system}.dovetail-seams;

          # The show verb's unit tests over the targeting rule, which run
          # in the package's own check phase — so this check is the
          # package, and a rule that misranks instances fails the build.
          show-unit = self.packages.${system}.dovetail-show;

          # The show verb end to end, for the path a sandbox can reach:
          # the caller names a socket, and the file lands in that
          # instance. The other two steps of the rule need a compositor.
          show-explicit-socket = pkgs.callPackage ./nix/checks/show-explicit-socket.nix {
            dovetail-nvim = self.packages.${system}.dovetail;
            dovetail-show = self.packages.${system}.dovetail-show;
          };

          # The launch path's failure detection, for the no-compositor
          # case the sandbox actually is: a terminal that dies instead of
          # opening anything fails the invocation loudly, rather than the
          # silent, zero-exit-status success this used to be.
          show-launch-failure = pkgs.callPackage ./nix/checks/show-launch-failure.nix {
            dovetail-show = self.packages.${system}.dovetail-show;
          };

          # The scriptorium verb's unit tests over the scratch file
          # convention, the layout rule and the order the steps run in.
          scriptorium-unit = self.packages.${system}.dovetail-scriptorium;

          # The run verb's unit tests over what it refuses, the
          # provenance block and the argv the terminal is handed, which
          # run in the package's own check phase — so this check is the
          # package.
          run-unit = self.packages.${system}.dovetail-run;

          # The prompt itself, driven under a pty: pressing Enter on the
          # pre-filled line runs exactly the command that was displayed,
          # an edited line runs the edited line, and a cleared line runs
          # nothing. This is the one claim of the verb, checked against a
          # real bash rather than asserted.
          run-prompt = pkgs.callPackage ./nix/checks/run-prompt.nix {
            dovetail-run = self.packages.${system}.dovetail-run;
          };

          # The run verb's launch path, for the no-compositor case the
          # sandbox is: a terminal that dies fails the invocation loudly,
          # and everything refusable is refused before any terminal is
          # spawned at all.
          run-launch-failure = pkgs.callPackage ./nix/checks/run-launch-failure.nix {
            dovetail-run = self.packages.${system}.dovetail-run;
          };

          # The scriptorium end to end, for the path a sandbox can reach:
          # no compositor, so no layout — but a real editor holding the
          # real scratch file, asked over RPC which file it has open.
          scriptorium-room = pkgs.callPackage ./nix/checks/scriptorium-room.nix {
            dovetail-nvim = self.packages.${system}.dovetail;
            dovetail-scriptorium = self.packages.${system}.dovetail-scriptorium;
          };
        }
      );

      devShells = forAllSystems (
        { pkgs, ... }:
        {
          default = pkgs.mkShellNoCC {
            packages = [
              pkgs.nixfmt
              pkgs.nix-tree
            ];
          };
        }
      );

      formatter = forAllSystems ({ pkgs, ... }: pkgs.nixfmt);
    };
}
