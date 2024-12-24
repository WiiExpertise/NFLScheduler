# -*- coding: utf-8 -*-
"""
Created on Wed Apr 20 14:55:35 2016

@author: M
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Mar 30 08:34:54 2016

@author: John
"""
import csv
import json 
from gurobipy import *

import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# Read the JSON file
with open(resource_path('auxiliaryLookup.json'), 'r') as json_file:
    data = json.load(json_file)

H = {}
myFile = open(resource_path('Opponents 17G Season 2016.csv'),'rt')
myReader = csv.reader(myFile)    
for row in myReader:
    if row[0] != 'Away Team':
        
        if row[1] in H:
            H[row[1]].append(row[0])
        else:
            H[row[1]] = [row[0]]

myFile.close()


A = {}
myFile = open(resource_path('Opponents 17G Season 2016.csv'),'rt')
myReader = csv.reader(myFile) 
for row in myReader:
    if row[0] != 'Away Team':
        
        if row[0] in A:
            A[row[0]].append(row[1])
        else:
            A[row[0]] = [row[1]]
        

myFile.close()

S = {}
myFile= open(resource_path('Slots17.csv'))
myReader = csv.reader(myFile)
for row in myReader:
    for cell in row:
        if len(cell)!=0 and cell!=row[0]:
            if int(row[0]) in S:
                S[int(row[0])].append(cell)
            else:
                S[int(row[0])]=[cell]

del(row,cell)
myFile.close()

T = ['DAL', 'NYG', 'PHI','WAS','CHI', 'DET', 'GB','MIN','ATL','CAR','NO','TB',
     'ARZ','LAR','SF','SEA','BUF','MIA','NE','NYJ','BAL','CIN','CLE','PIT',
     'HOU','IND','JAC','TEN','DEN','KC','OAK','SD']

     
DIVISION = {'NFC':{'NEAST':['DAL', 'NYG', 'PHI','WAS'],
                   'NNORTH':['CHI', 'DET', 'GB','MIN'],
                   'NSOUTH':['ATL', 'CAR','NO','TB'],
                   'NWEST':['ARZ','LAR','SF','SEA']
                   },
            'AFC':{'AEAST': ['BUF','MIA','NE','NYJ'],
                   'ANORTH': ['BAL','CIN','CLE','PIT'],
                   'ASOUTH': ['HOU','IND','JAC','TEN'],
                   'AWEST': ['DEN','KC','OAK','SD']            
                   }
            }
CONFERENCE = {'NFC':['DAL', 'NYG', 'PHI','WAS','CHI', 'DET', 'GB','MIN','ATL','CAR','NO','TB','ARZ','LAR','SF','SEA'],
              'AFC':['BUF','MIA','NE','NYJ','BAL','CIN','CLE','PIT','HOU','IND','JAC','TEN','DEN','KC','OAK','SD']
            }
            
myModel = Model()
myModel.update()
            
##OBJECTIVE FUNCTION##
myGames = {}
for h in T:
    for a in H[h]:
        for w in range(1,19):
            for s in S[w]:
                myGames[a,h,s,w] = myModel.addVar(obj =1, vtype=GRB.BINARY, 
                                    name='games_%s_%s_%s_%s' % (a,h,s,w))

for h in T:
    for w in range(4,14):
        myGames['BYE',h,'SUNB_NFL',w] = myModel.addVar(obj =1, vtype=GRB.BINARY, 
                                        name='games_BYE_%s_%s_%s' % (h,s,w))

myModel.update()                                        

myModel.setObjective(quicksum(myGames[a,h,s,w,] for w in range(1,19) for h in T for a in H[h] for s in S[w]),GRB.MINIMIZE)
########################################################################################################################

## CONSTRAINTS
myConstr = {}

#constraint 1: every game played once 
for h in T: #iterate over all 32 teams (a,h)
    for a in H[h]: #each away team
        constrName = '1_game_once_%s_%s' % (a,h)
        myConstr[constrName] = myModel.addConstr(quicksum(myGames[a,h,s,w]
                                        for w in range (1,19) for s in S[w]) == 1,
                                        name = constrName)
myModel.update()  
                                                                          
#constraint 2: teams play one game each week (takes care  of everything but bye games)
for t in T:
    for w in [1,2,3,14,15,16,17,18]:
        constrName = '1_in_w%s_by_%s' % (w,t)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,t,s,w] for a in H[t] for s in S[w]) 
                            + quicksum(myGames[t,h,s,w] for h in A[t] for s in S[w]) == 1, 
                            name=constrName)
myModel.update()
        
#constraint 3: teams play one game each week (takes care of bye games)
for t in T:
    for w in range(4,14):
        constrName = '1_bye_in_w%s_by_%s' %(w,t)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,t,s,w] for a in H[t] for s in S[w] if s != 'SUNB_NFL') 
        + quicksum(myGames[t,h,s,w] for h in A[t] for s in S[w] if s != 'SUNB_NFL') 
        + myGames['BYE',t, 'SUNB_NFL', w] == 1, name=constrName)
myModel.update()
        
#constraint 4:No more than 6 bye games in a given a week
for w in range(4,14):
    constrName = '4_Bye_game_by_%s_in_w%s' % (t,w)
    myConstr[constrName]=myModel.addConstr(quicksum(myGames['BYE',t,'SUNB_NFL',w] for t in T)<=6, name=constrName)

w = None
myModel.update()

#contraint 5: No team that had an early bye game (week 4) in 2015 can have an early bye game (week 4) in 2016
constrName = 'TEN,NE do not play in week 4'
myConstr[constrName]=myModel.addConstr(myGames['BYE','NE','SUNB_NFL',4] + myGames['BYE','TEN','SUNB_NFL',4]==0,
name=constrName)
myModel.update()

#constraint 6: Exactly 1 Thursday game every week upto week 16, week 17 has no thursday games
Thursday = ['THUN_NBC' , 'THUN_NFL' , 'THUN_NFL' , 'THUE_FOX' ,'THUL_CBS', 'THUN_NBC' , 'THUN_CBS'  ]
for w in range(1, 18):
    for s in S[w]:
        if s in Thursday:
            constrName = '6_one_Thursday_in_w%s' % (w)
            if w == 12:
                constrName2 = '6_one_DALDET_in_w%s' % (w)
                # Adding specific conditions for Week 12
                if s == 'THUE_FOX':
                    myConstr[constrName2] = myModel.addConstr(
                        quicksum(myGames[a, h, s, w] for h in ['DET'] for a in H[h]) == 1, name=constrName)
                elif s == 'THUL_CBS':
                    myConstr[constrName2] = myModel.addConstr(
                        quicksum(myGames[a, h, s, w] for h in ['DAL'] for a in H[h]) == 1, name=constrName)
                    
                myConstr[constrName] = myModel.addConstr(
                    quicksum(myGames[a, h, s, w] for h in T for a in H[h]) == 1, name=constrName)
            else:
                # For other weeks, the constraint remains the same
                myConstr[constrName] = myModel.addConstr(
                    quicksum(myGames[a, h, s, w] for h in T for a in H[h]) == 1, name=constrName)
myModel.update()

#constraint 7:There are two Saturday Night Games in Week 15 (one SatE and one SatL)
for s in ['SATE_NFL','SATL_NFL']:
    constrName='2_Games_on_Sat_s%s' %(s)
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,15] for h in T for a in H[h]) == 1,name=constrName)
myModel.update()

#constraint 8: There is only one “double header” game in weeks 1 through 16 (and two in week 17)
#Week 1:16
for w in range(1,18):
    for s in ['SUNDH_CBS','SUNDH_FOX']:
        constrName= '1_DH_in_w%s%s' %(w,s)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w] for h in T for a in H[h]) == 1, name=constrName)
myModel.update()
 
#Week 17   
constrName='2_DH_in_17'
myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,18] for h in T for a in H[h] for s in ['SUNDH_CBS','SUNDH_FOX']) == 2,name=constrName)
myModel.update()

#constraint 9: There is exactly one Sunday Night Game in weeks 1 through 16 (no Sunday Night Game in week 17)
#Week 1:16
for w in range(1,18):
    constrName='1_SundayNight_in_w%s' %w
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,'SUNN_NBC',w] for h in T for a in H[h]) == 1,name=constrName)
myModel.update()

#constraint 10 Part 1: There are two Monday night games in week 1
WC=['SD', 'SF', 'SEA', 'OAK', 'LAR']

constrName='2_Mondays_in_w1'
myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,1]for h in T for a in H[h] for s in ['MON0_ESPN','MON2_ESPN']) == 2,name=constrName)
myModel.update()

#constraint 10 Part 2: The late Monday Night Game must be hosted by a West Coast Team (SD, SF, SEA, OAK, LAR)
 #List of west coast teams

for w in range(1,2):
    if s in S[w]:
        constrName='%s_slot_w%s' %(s,w)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,'MON2_ESPN',w] for h in WC for a in H[h]) == 1, name=constrName)
myModel.update()

#constraint 10 Part 3: There in exactly one Monday night game in weeks 2 through 16 (no Sunday Night Game in week 17))
# Week 2:16
for w in range(2,18):
    constrName='1_Monday_in_w%s' %(w)
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,'MON1_ESPN',w] for h in T for a in H[h]) ==1 , name=constrName)
myModel.update()

#constraint 11: West Coast (SD, SF, SEA, OAK, LAR) and Mountain Teams (DEN, ARZ) cannot play at home in the early Sunday time slot
MT=['DEN','ARZ']
WCMT=WC+MT

for w in range(1,19):
    constrName='WstCst_MtTm_cannot_SUNE_w%s' %(w)
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w] for h in WCMT for a in H[h] for s in ['SUNE_CBS','SUNE_FOX'])==0,name=constrName)
myModel.update()
    
#constraint 12_Home_Games: No team plays 4 consecutive home/away games in a season (treat a BYE game as an away game)
for w in range(1,16):
    for h in H:
       constrName ='no_more_than_4_consecutive_games_in_w%s_at_h%s' %(w,h)
       myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w1] for a in H[h] for w1 in range(w, w+4) for s in S[w1]) <= 3, name = constrName)
myModel.update()

#constraint 12_Away_Games:
for w in range(1,16):
    for a in A:
       constrName ='no_more_than_4_consecutive_games_w%s_at_a%s' %(w,a)
       myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w1] for h in A[a] for w1 in range(w, w+4) for s in S[w1]) +
                                              quicksum(myGames[a,'BYE',s,w1] for w1 in range(w, w+4) for s in S[w1] if (a,'BYE',s,w1) in myGames) <= 3, name = constrName)
myModel.update()

#constraint 13a_Home_Games: No team plays 3 consecutive home/away games during the weeks 1, 2, 3, 4, 5 and 15, 16, 17 (treat a BYE game as an away game)
for w in range(1,4):
    for h in H:
        constrName ='no_more_than_4_consecutive_games_1_5_w%s_at_h%s' %(w,h)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w1] for a in H[h] for w1 in range(w, w+3) for s in S[w1]) <= 2, name = constrName)    
myModel.update()

#Constraint 13a_Away_Games:
for w in range(1,4):
    for a in A:
        constrName ='no_more_than_4_consecutive_games_1_5_w%s_at_a%s' %(w,a)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w1] for h in A[a] for w1 in range(w, w+3) for s in S[w1]) +
                                               quicksum(myGames[a,'BYE',s,w1] for w1 in range(w, w+3) for s in S[w1] if (a,'BYE',s,w1) in myGames)<= 2, name = constrName) 
myModel.update()
        
#constraint 13b_Home_Games:
for h in H:
    constrName ='no_more_than_4_consecutive_games_15_18_w15_%s' %h
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w] for a in H[h] for w in range(15, 19) for s in S[w]) <= 2, name = constrName)
    #need to add bye games
myModel.update()

#constraint 13b_Away_Games:
for a in A:
    constrName ='no_more_than_4_consecutive_games_15_18_w15_%s' %a
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w] for h in A[a] for w in range(15, 19) for s in S[w]) +
                                           quicksum(myGames[a,'BYE',s,w] for w in range(15, 19) for s in S[w] if (a,'BYE',s,w) in myGames)<= 2, name = constrName)
myModel.update()

#constraint 14_Home_Games: Each team must play at least 2 home/away games every 6 weeks
for w in range(1,14):
    for h in H:
        constrName ='at_least_2games_per6weeks_w%s_at_h%s' %(w,h)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w1] for a in H[h] for w1 in range(w, w+6) for s in S[w1]) >= 2, name = constrName)
myModel.update()

#constraint 14_Away_Games
for w in range(1,14):
    for a in A:
        constrName ='at_least_2games_per6weeks_w%s_at_a%s' %(w,a)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w1] for h in A[a] for w1 in range(w, w+6) for s in S[w1]) +
                                               quicksum(myGames[a,'BYE',s,w1] for w1 in range(w, w+6) for s in S[w1] if (a,'BYE',s,w1) in myGames)>= 2, name = constrName)
myModel.update()

#constraint 15: Each team must play at least 4 home/away games every 10 weeks
for w in range(1,8): #adding 10 weeks goes beyond week 17
    for h in H:
        constrName ='at_least_4home_every10weeks_w%s_h%s' %(w,h)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w1] for a in H[h] for w1 in range(w, w+11) for s in S[w1]) >= 4, name = constrName)
myModel.update()

for w in range(1,8):
    for a in A:
        constrName ='at_least_4away_every10weeks_w%s_h%s' %(w,a)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w1] for h in A[a] for w1 in range(w, w+11) for s in S[w1]) +
                                               quicksum(myGames[a,'BYE',s,w1] for w1 in range(w, w+11) for s in S[w1] if (a,'BYE',s,w1) in myGames) >= 4, name = constrName)
myModel.update()  

#Constraint 16:Superbowl champion from 2015 opens the season at home on Thursday night of Week 1
for h in H:
    for a in H[h]:
        for s in S[1]:
                if s[:4] == "THUN" and h!= data['superBowlChampion']:
                        myModel.remove(myGames[a,h,s,1])
                        del myGames[a,h,s,1]
                        

myModel.update() 

# Corrected Constraint 17: Ensure all Week 18 games are divisional
for h in T:
    for a in T:
        if h != a:
            # Identify the divisions for home and away teams
            h_division = next((division for conference, divisions in DIVISION.items()
                               for division, teams in divisions.items() if h in teams), None)
            a_division = next((division for conference, divisions in DIVISION.items()
                               for division, teams in divisions.items() if a in teams), None)
            
            # If home and away teams are not in the same division, prohibit the game in Week 18
            if h_division != a_division:
                for s in S[18]:  # All slots for Week 18 (outside of the `if` condition)
                    # Check if myGames[h, a, s, 18] exists before creating a constraint
                    if (a, h, s, 18) in myGames:
                        constrName = f'same_division_week_18_{a}_vs_{h}_slot_{s}'
                        myConstr[constrName] = myModel.addConstr(myGames[a, h, s, 18] == 0, name=constrName)
                    #else:
                        # Optional debug output to track missing entries
                        #print(f"Skipping constraint for non-existent game entry: ({a}, {h}, {s}, 18)")
            #else:
                # Debug output to track same division games
                #print(f"Same division game: {h} vs {a}")
                #print(f"Divisions: {h_division} vs {a_division}")
            
myModel.update()

# Constraint: No team plays each other in back-to-back games
for t1 in T:
    for t2 in T:
        if t1 != t2:  # Ensure different teams
            for w in range(1, 18):  # Iterate over weeks
                for s1 in S[w]:  # Iterate over slots in week w
                    for s2 in S[w+1]:  # Iterate over slots in week w+1
                        if (t1, t2, s1, w) in myGames and (t2, t1, s2, w+1) in myGames:
                            constrName = 'no_back_to_back_games_%s_%s_before_w%s_%s_%s' % (t1, t2, w, s1, s2)
                            myConstr[constrName] = myModel.addConstr(
                                myGames[t1, t2, s1, w] + myGames[t2, t1, s2, w+1] <= 1,
                                name=constrName
                            )
myModel.update()

# Constraint: No team plays in specific slots in back-to-back weeks
PrimetimeSlots = ['THUN_NFL', 'THUN_NBC', 'THUN_CBS', 'SUNN_NBC', 'MON0_ESPN', 'MON1_ESPN', 'MON2_ESPN'] 
for t in T:  # Iterate over teams
    for w in range(1, 18):  # Iterate over weeks (up to week 16 to avoid out of range error)
        for s in S[w]:  # Iterate over slots in week w
            if s in PrimetimeSlots:  # Check if the slot is in the list of restricted slots
                # Check if there's a next week and if the team plays in the same slot next week
                if w + 1 <= 18 and s in S[w + 1]:
                    constrName = 'no_back_to_back_slots_%s_in_%s_w%s_w%s' % (t, s, w, w + 1)
                    myConstr[constrName] = myModel.addConstr(
                        quicksum(myGames.get((t, a, s, w), 0) + myGames.get((a, t, s, w), 0) for a in T) + 
                        quicksum(myGames.get((t, a, s, w + 1), 0) + myGames.get((a, t, s, w + 1), 0) for a in T) <= 1,
                        name=constrName
                    )
myModel.update()

#Objective 2: Minimize the number of division series that end in the first half of the season.  
#OBJECTIVE FUNCTION##

myModel.update()
myModel.optimize()
myModel.write('solution.json')
#    
#dirtyHarris= {'Good':['DAL', 'GB', 'PHI','NE','DEN','PIT','SEA','CHI','NYG','SF','NO'],
#              'Bad':['ARZ', 'ATL', 'WAS','MIN', 'PHI','OAK','CAR','MIA','IND','BUF','DET'],
#              'Ugly':['NYJ', 'BAL','MIN','HOU','CIN','KC','CLE','TB','TEN','SD','LAR','JAC']}
#
#slotVal={}
#for w in S:
#    for s in S[w]:
#        if 'SUNDH' in s:
#            print 1,s
#            slotVal[s]=6
#        elif 'SUNN' in s:
#            print 2,s
#            slotVal[s]=5
#        elif 'SUNE' or 'SUNL' or 'SAT' in s:
#            print 3,s
#            slotVal[s]=1    
#        elif 'THUN_NBC' or 'THUN_CBS' in s:
#            print 3,s
#            slotVal[s]=4
#        elif 'THUN_NFL' in s:
#            slotVal[s]=2
#        elif 'MON' in s:
#            slotVal[s]=3
#        else:
#            slotVal[s]=0
#            
#
#harrisModel=Model()
#harrisGames={}
#for amigo in T:
#    for enemigo in H[amigo]:
#        for w in range(1, 18):
#            for s in S[w]:
#                if amigo in dirtyHarris['Good'] or enemigo in dirtyHarris['Good']:
#                    harrisGames[enemigo,amigo,s,w] = Harris.addVar(obj =4, vtype=GRB.BINARY, 
#                                    name='games_%s_%s_%s_%s' % (enemigo,amigo,s,w))
#                elif amigo in dirtyHarris['Bad'] or enemigo in dirtyHarris['Bad']:
#                    harrisGames[enemigo,amigo,s,w] = Harris.addVar(obj =2, vtype=GRB.BINARY, 
#                                    name='games_%s_%s_%s_%s' % (enemigo,amigo,s,w))
#                elif amigo in dirtyHarris['Ugly'] or enemigo in dirtyHarris['Ugly']:
#                    harrisGames[enemigo,amigo,s,w] = Harris.addVar(obj =1, vtype=GRB.BINARY, 
#                                    name='games_%s_%s_%s_%s' % (enemigo,amigo,s,w))
#harrisModel.update()                                    
#                    
#lenght = 0               
#for sol in myGames:
#...    if myGames[sol].x>0:
#...         length =+1