{
  description = "HRI CW 2";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/23.05";
  };

  outputs = { self, nixpkgs }: 
  let 
    # system = "aarch64-darwin";
    system = "x86_64-linux";

    pyGameDevShell = system: nixpkgs.legacyPackages.${system}.mkShell rec {
      name = "CookRobotENV";

      packages = with nixpkgs.legacyPackages.${system}; [ 
        python311Packages.pygame
      ];

      shellHook = ''
        export PS1="\e[0;31m[\u@\h \W]\$ \e[m " 
      '';
    };

  in
  {
    devShells."x86_64-linux".default = pyGameDevShell "x86_64-linux";
    devShells."aarch64-darwin".default = pyGameDevShell "aarch64-darwin";
  };
}
