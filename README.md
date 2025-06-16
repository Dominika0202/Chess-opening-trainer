# Opening Trainer Project
In this project we use the data from lichess.org database and the streamlit library to build an interactive chess opening trainer and to present insightful statistics about piece movement. We focus on the games played on the website in March 2025 by highly rated players (ELO 2400+). 

# Cleaning of the Data
The original compressed file is of the size 30GB. It is in the pgn format, which is standard for chess games. <br />
As the original file is too large to share and the cleaning the whole file takes a substantial amount of time, we provide a sample of 1000 games to try out the cleaning code.

Example game <br />
[Event "Rapid swiss https://lichess.org/swiss/7siKNYGN"] <br />
[Site "https://lichess.org/ECy8BFok"] <br />
[Date "2025.03.01"] <br />
[Round "-"] <br />
[White "STRI0006"] <br />
[Black "PORT0024"] <br />
[Result "1-0"] <br />
[UTCDate "2025.03.01"] <br />
[UTCTime "00:00:00"] <br />
[WhiteElo "939"] <br />
[BlackElo "404"] <br />
[WhiteRatingDiff "+3"] <br />
[BlackRatingDiff "-4"] <br />
[ECO "C41"] <br />
[Opening "Philidor Defense"] <br />
[TimeControl "600+0"] <br />
[Termination "Normal"] <br />
<br />
1\. e4 { [%eval 0.18] [%clk 0:10:00] } 1... e5 { [%eval 0.21] [%clk 0:10:00] } 2. Nf3 { [%eval 0.13] [%clk 0:09:59] } 2... d6 { [%eval 0.48] [%clk 0:10:00] } 3. Nc3 { [%eval 0.28] [%clk 0:09:57] } 3... Nc6 { [%eval 0.56] [%clk 0:09:52] } 4. Bc4 { [%eval 0.29] [%clk 0:09:55] } 4... Be6 { [%eval 0.42] [%clk 0:09:43] } 5. Bxe6 { [%eval 0.41] [%clk 0:09:53] } 5... fxe6 { [%eval 0.33] [%clk 0:09:42] } 6. d3 { [%eval 0.19] [%clk 0:09:49] } 6... d5? { [%eval 1.56] [%clk 0:09:29] } 7. exd5?! { [%eval 0.92] [%clk 0:09:48] } 7... Nb4? { [%eval 3.42] [%clk 0:09:02] } 8. dxe6 { [%eval 3.32] [%clk 0:09:42] } 8... Nxd3+? { [%eval 6.02] [%clk 0:08:59] } 9. cxd3 { [%eval 6.29] [%clk 0:09:40] } 9... Bb4 { [%eval 8.18] [%clk 0:08:46] } 10. Bg5 { [%eval 6.43] [%clk 0:09:36] } 10... Qd7?? { [%eval 14.09] [%clk 0:08:42] } 11. exd7+ { [%eval 13.67] [%clk 0:09:35] } 11... Kxd7 { [%eval 12.74] [%clk 0:08:40] } 1-0

We retain only some of the information about the game for our analysis, specifically: Site, White, Black, Result, White and Black Elo, Eco, Opening, Time Control, Termination and the Moves. From the Site field we extract the unique ID (the characters following the last /), which serves as game identifier. Moreover, we clean the move data by removing, to us, unnecessary annotation like evaluation of the position and click time. Furthermore, we strip the moves of the identification of Black’s moves (a number followed by 3 dots).

Further we clean the games by removing the ones that were "Unterminated", terminated by "Rules infraction" (e.g. cheating) or "Abandoned". Also we remove the games that had no moves (e.g. when an opponent gave up before the start of the game) and the we put the Time Control values into categories (Bullet, Blitz...), we follow the website rules found here
https://lichess.org/faq#time-controls.

The resulting data is stored in a compressed CSV file of a size about 500 MB. This file can be found in the shared data_set_link.txt file.
## Home Page
The home page serves to introduce the user to the webiste and show some basic statistical properties of the chosen dataset. These statistics include total games, unique openings and average game length (measured in moves) present within the dataset.
## Opening Trainer

We take two approaches to identify the games which played the desired position.
In the first approach we compare the desired move string with the moves in each game in our dataset. That is, we filter the games that played the exact same sequence of moves. This opproach is quite fast, however not very precise as in chess 
the same position can be reached by a different sequence of moves. We encode this approach within the **Simple Trainer** tab.

In the second approach, we calculate a so called FEN (Forsyth–Edwards Notation) string. FEN is a single‐line text format that uniquely describes a chess position. Our FEN string has six fields, separated by spaces:
- Piece placement
- Active color (“w” or “b”)
- Castling rights (e.g. “KQkq” or “–”)
- En passant target square (e.g. “e3” or “–”)

Since our focus is only on openings the FEN string is calculated for the first 15 moves of each game. Calculating a FEN string for each position is both memory intensive and computationally slow, but it is crucial for accurately identifying positions played in the game. This allows us to find precise statistics like the most popular next moves or opening insights after the user inputs the desired position. This approach, we encode within the **Advanced Trainer** tab.

---

## Statistics

The **Statistics** page is an interactive page that displays statistics sampled from 50.000 chess games from the chosen dataset. It enables users to explore player performance, game characteristics, and popularity across various openings.

### Tabs

Each tab provides a select statistical view:

- **ELO Distribution**  
  Displays the distribution of player Elo ratings by combining both White and Black ratings. Useful for understanding player strength in the dataset.

- **Opening Popularity**  
  Shows the top 25 most frequently played chess openings, ranked by total games.

- **Game Results**  
  A pie chart of game outcomes (White wins, Black wins, Draws), showing the balance of results across the dataset.

- **Game Duration**  
  Visualizes how many moves games typically last using a histogram of total move counts.

- **Win Rate by Opening**  
  Compares opening performance based on win rates for White and Black. Users can filter by minimum number of games and choose which side’s win rate to rank by.

- **Termination Types**  
  Highlights the top 10 reasons games ended (e.g., checkmate, resignation, timeout), showing conclusion statistics in the dataset.

- **Time Controls**  
  Displays the 10 most common time control formats used in the dataset, which shows preferred pacing among players in the dataset (e.g., blitz, rapid).