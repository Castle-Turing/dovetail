{
  description = "Dovetail — the editor joint: a nixvim module whose every instance is born reachable over a socket";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    nixvim = {
      url = "github:nix-community/nixvim";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      nixvim,
    }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
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
      # without adopting any module system.
      packages = forAllSystems (
        { system, ... }:
        rec {
          dovetail = (evalDovetail { inherit system; }).config.build.package;
          default = dovetail;
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
        }
      );

      devShells = forAllSystems (
        { pkgs, ... }:
        {
          default = pkgs.mkShellNoCC {
            packages = [
              pkgs.nixfmt-rfc-style
              pkgs.nix-tree
            ];
          };
        }
      );

      formatter = forAllSystems ({ pkgs, ... }: pkgs.nixfmt-rfc-style);
    };
}
