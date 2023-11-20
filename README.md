# HRI-CW2

Report:
https://www.overleaf.com/6819461832smnccntpqrkg#225550

Repo:
https://github.com/RobbieBuxton/HRIcw2

## Code setup
For all questions the required python modules need to be installed. No additional modules are required, only those required by the base Cookbot game (pygame, numpy) or modules included in the standard library.
Additionally, ensure you are using python 3.10.11 or later

## Q1
To run the code for the HMM run the command:

    python .\Cookbot_HMM.py

This will print to the console as it runs with some prediciton information.
Additionally the file state_prob.txt will be prduced which will contain the lists of predicted states, real user states and the accuracy of the HMM

## Q2
To run the coop code run the command:

    python .\Cookbot_Coop.py

This code will print to the console the robots current state which you may inspect.
The robot will act as optimally as it can, but requires the player to be helping since it cannot reach all the components itself.

## Q3
To run the conditions code for the user study run the command:

    python .\Cookbot_Conditions.py

You will be prompted in the terminal to enter a number 0-3 inclusive.
To view the tutorial stage enter 0
To view condition 1 enter 1
To view condition 2 enter 2
To view condition 3 enter 3
For the actual user study we will control the condition of the user to assign the order they experience each condition in.
After entering a number, the game will begin in the pygame window.
Once the timer expires the user's final score will be printed to the terminal
