; CHESS.ASM
; ENIAC chess - the best game for the first computer
; By Jonathan Stray and Jered Wierzbicki
; 
; This is the main game file which includes and places all routines and does the search.
; It is a 4-ply minimax search with alpha/beta pruning and simple material scoring,
; and no special opening or endgame logic. ENIAC always plays white.
;
; This file, like all asm files in this project, is written in the custom VM language
; It is assembled by chasm.py into simulator switch settings chess.e, concatenated 
; with VM wiring patch setup chessvm.e, and then executed by eniacsim. 

  .isa v4
  .include memory_layout.asm

  .org 100
  .section i
  jmp far game       ; the game outer loop is in ft3

  .section g
  .include movegen.asm
  .section b
  .include get_square.asm

  .org 200
  .section m
  .include move.asm

; Main program - we jump here on reset
  .org 306

game
  ; set memory state from cards
  ; assume this includes the human player's move
  .section i
  .include load_board.asm

start
  .section s
  .include search.asm

  .section i
search_done
  ; print the best move found during the search
  mov BEST,A
  loadacc A           ; I=bestfrom, J=bestto
  mov J,A
  swap A,B
  mov I,A
  print

  ; Update board so GUI shows it, then jumps to game
  .include make_eniac_move.asm
