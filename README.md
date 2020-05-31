## Five Crowns Interactive Game Teaching Project

Creating a teaching project for Girl Scout "Coding For Good - Gaming" badge requirements.

Python illustrative implementation of a client / server game structure.

Working pseudocode documentation:
https://docs.google.com/document/d/1RpmL6ycQe_bQEFvb1K7RBbWh_zIMzNlYEs1hjJ8b8JI/edit?usp=sharing

Credit:
The game was created by Set Enterprises in 1996, Set Enterprises is PlayMonster, LLC company.
All rights reserved by PlayMonster, LLC.

#### Version History

Summary of functionality through 2020-05-24

    + added postgame reporting

    + add log files and cleaned up game exit

    + grouping of cards on round-ending scoring page

    + disabling the "Score Remaining Cards" button after books/runs are created until they are accepted (or rejected)

    + running and per round score added, along with winner at end of game
        
    + new "grouping dialog" added after going out to form books and runs

    + took a guess at the cause of last week's dialog closing bug and added some code to help
    
    + added "star suit" and two extra jokers in keeping with the original deck specs

    + functional now, albeit without scoring or book / run tagging  
    
    + UI messaging, dealing and discard completed (need to debug the later two)
    
    + components of player UI, less how to 'mark' runs and books, complete
    
    + using pyqt5 to build UI; reorderable player hand completed

    + api tested up to out validation / scoring
    
    + initial commit with skeletal barebones ability to serve via localhost

#### ACTIVE To-Dos    
    + github authentication token and use of google cloud environmental variables    

    + replace flask templating with jinja2 in fc module    

    + clean up final report and decide if server sends the emails
        
    + put a "IS GROUPING" status comment up when player is grouping cards
    
    + add a way for players to "check out" when they close the client app
    so that the server knows when to shut down the game
    
    + get emails off github (use ini or pickle)
    
    + ability to restart the game at any round number
    
    + ability to rejoin the game and retain your (server) hand
        
    + redo server to Flash's API template
    
    + use sockets to eliminate "refresh" client/server model design
    
#### COMPLETED To-Dos    
    
    + revised final score email to include simple analytics 
    
    + email final score HTML to all players 
    
    + use of log files for the client instead of stdout.  
    maybe client startup process sends the current log file to the server and then truncates it.

    + scoring added with winner 
    
    + move refresh button under discard group
    
    + crashing bug that appears in client as dialogs that won't dismiss or repopulate

    + automate invite game starting process (so others can execute)
    
    + non-modal dialogs should stay on top

    + bug: cards at the beginning of a new round are bogus until you draw

    + bug: dealer seems to be the active player after starting new round 
