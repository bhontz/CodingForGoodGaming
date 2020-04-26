## Five Crowns Interactive Game Teaching Project

Creating a teaching project for Girl Scout "Coding For Good - Gaming" badge requirements.

Python illustrative implementation of a client / server game structure.

Working pseudocode documentation:
https://docs.google.com/document/d/1RpmL6ycQe_bQEFvb1K7RBbWh_zIMzNlYEs1hjJ8b8JI/edit?usp=sharing

Credit:
The game was created by Set Enterprises in 1996, Set Enterprises is PlayMonster, LLC company.
All rights reserved by PlayMonster, LLC.

#### Version History

Summary of functionality through 2020-04-26

    + took a guess at the cause of last week's dialog closing bug and added some code to help
    
    + added "star suit" and two extra jokers in keeping with the original deck specs

    + functional now, albeit without scoring or book / run tagging  
    
    + UI messaging, dealing and discard completed (need to debug the later two)
    
    + components of player UI, less how to 'mark' runs and books, complete
    
    + using pyqt5 to build UI; reorderable player hand completed

    + api tested up to out validation / scoring
    
    + initial commit with skeletal barebones ability to serve via localhost

#### ACTIVE To-Dos
 
    + use of log files for the client instead of stdout.  
    maybe client startup process sends the current log file to the server and then truncates it.

    + ability to rearrange cards after going out, including tagging books and runs
    
    + ability to restart the game at any round number
    
    + ability to rejoin the game and retain your (server) hand
        
    + redo server to Flash's API template
    
#### COMPLETED To-Dos    

    + (NEEDS TESTING TO CONFIRM) crashing bug that appears in client as dialogs that won't dismiss or repopulate

    + automate invite game starting process (so others can execute)
    
    + non-modal dialogs should stay on top

    + bug: cards at the beginning of a new round are bogus until you draw

    + bug: dealer seems to be the active player after starting new round 
