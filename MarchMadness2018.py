# Format: 
# 1) Imports
# 2) Load Training Set and CSV Files
# 3) Train Model
# 4) Test Model
# 5) Create Kaggle Submission

############################## IMPORTS ##############################

from __future__ import division
import sklearn
import pandas as pd
import numpy as np
import collections
import os.path
from sklearn.cross_validation import train_test_split
from sklearn import svm
from sklearn.svm import SVC
from sklearn import linear_model
from sklearn import tree
from sklearn.cross_validation import cross_val_score
from keras.utils import np_utils
from sklearn.neighbors import KNeighborsClassifier
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.ensemble import GradientBoostingClassifier
import sys
from sklearn.ensemble import GradientBoostingRegressor
import math
import csv
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import classification_report
from sklearn.calibration import CalibratedClassifierCV
import urllib
from sklearn.svm import LinearSVC
import xgboost as xgb
from sklearn.model_selection import GridSearchCV
from datetime import datetime
import random

############################## LOAD TRAINING SET ##############################

if os.path.exists("Data/PrecomputedMatrices/xTrain.npy") and os.path.exists("Data/PrecomputedMatrices/yTrain.npy"):
	xTrain = np.load("Data/PrecomputedMatrices/xTrain.npy")
	yTrain = np.load("Data/PrecomputedMatrices/yTrain.npy")
	print ("Shape of xTrain:", xTrain.shape)
	print ("Shape of yTrain:", yTrain.shape)
else:
	print ('We need a training set! Run dataPreprocessing.py')
	sys.exit()

############################## LOAD CSV FILES ##############################

sample_sub_pd = pd.read_csv('Data/KaggleData/SampleSubmissionStage1.csv')
sample_sub_pd2 = pd.read_csv('Data/KaggleData/SampleSubmissionStage2.csv')
teams_pd = pd.read_csv('Data/KaggleData/Teams.csv')

############################## TRAIN MODEL ##############################

model = GradientBoostingRegressor(n_estimators=100, max_depth=5)

categories=['Wins','PPG','PPGA','PowerConf','3PG', 'APG','TOP','Conference Champ','Tourney Conference Champ',
           'Seed','SOS','SRS', 'RPG', 'SPG', 'Tourney Appearances','National Championships','Location']
accuracy=[]
numTrials = 0

for i in range(numTrials):
    X_train, X_test, Y_train, Y_test = train_test_split(xTrain, yTrain)
    startTime = datetime.now() # For some timing stuff
    results = model.fit(X_train, Y_train)
    preds = model.predict(X_test)

    preds[preds < .5] = 0
    preds[preds >= .5] = 1
    localAccuracy = np.mean(preds == Y_test)
    accuracy.append(localAccuracy)
    print ("Finished run #" + str(i) + ". Accuracy = " + str(localAccuracy))
    print ("Time taken: " + str(datetime.now() - startTime))
if numTrials != 0:
	print ("The average accuracy is", sum(accuracy)/len(accuracy))

############################## TEST MODEL ##############################

def predictGame(team_1_vector, team_2_vector, home, modelUsed):
    diff = [a - b for a, b in zip(team_1_vector, team_2_vector)]
    diff.append(home)
    # Depending on the model you use, you will either need to return model.predict_proba or model.predict
    # predict_proba = Linear Reg, Linear SVC
    # predict = Gradient Boosted, Ridge, HuberRegressor

    #return modelUsed.predict_proba([diff])[0][1]
    return modelUsed.predict([diff])[0]

############################## CREATE KAGGLE SUBMISSION ##############################

def loadTeamVectors(years):
	listDictionaries = []
	for year in years:
		curVectors = np.load("Data/PrecomputedMatrices/TeamVectors/" + str(year) + "TeamVectors.npy").item()
		listDictionaries.append(curVectors)
	return listDictionaries

def createPrediction(stage2 = False):
	if stage2:
		years = [2018]
		localPd = sample_sub_pd2
	else:
		# The years that we want to predict for
		years = range(2014,2018)
		localPd = sample_sub_pd

	if os.path.exists("result.csv"):
		os.remove("result.csv")
	listDictionaries = loadTeamVectors(years)
	print ("Loaded the team vectors")
	results = [[0 for x in range(2)] for x in range(len(localPd.index))]

	predictionModel = GradientBoostingRegressor(n_estimators=100, max_depth=5)
	predictionModel.fit(xTrain, yTrain)

	for index, row in localPd.iterrows():
		matchupId = row['ID']
		year = int(matchupId[0:4]) 
		teamVectors = listDictionaries[year - years[0]]
		team1Id = int(matchupId[5:9])
		team2Id = int(matchupId[10:14])
		team1Vector = teamVectors[team1Id] 
		team2Vector = teamVectors[team2Id]
		pred1 = predictGame(team1Vector, team2Vector, 0, predictionModel)
		pred = pred1.clip(0.,1.)
		results[index][0] = matchupId
		results[index][1] = pred
	results = pd.np.array(results)
	firstRow = [[0 for x in range(2)] for x in range(1)]
	firstRow[0][0] = 'ID'
	firstRow[0][1] = 'Pred'
	with open("result.csv", "wb") as f:
		writer = csv.writer(f)
		writer.writerows(firstRow)
		writer.writerows(results)

#createPrediction()
#createPrediction(stage2=True)

############################## PREDICTING 2018 BRACKET ##############################

def trainModel():
	model = GradientBoostingRegressor(n_estimators=100, max_depth=5)
	model.fit(xTrain, yTrain)
	return model

def randomWinner(team1, team2, modelUsed):
	year = [2018]
	teamVectors = loadTeamVectors(year)[0]
	team1Vector = teamVectors[int(teams_pd[teams_pd['TeamName'] == team1].values[0][0])]
	team2Vector = teamVectors[int(teams_pd[teams_pd['TeamName'] == team2].values[0][0])]
	prediction = predictGame(team1Vector, team2Vector, 0, modelUsed)
	for i in range(10):
		if (prediction > random.random()):
			print ("{0} Wins".format(team1))
		else:
			print ("{0} Wins".format(team2))


def findWinner(team1, team2, modelUsed):
	year = [2018]
	teamVectors = loadTeamVectors(year)[0]
	team1Vector = teamVectors[int(teams_pd[teams_pd['TeamName'] == team1].values[0][0])]
	team2Vector = teamVectors[int(teams_pd[teams_pd['TeamName'] == team2].values[0][0])]
	prediction = predictGame(team1Vector, team2Vector, 0, modelUsed)
	if (prediction < 0.5):
		print ("Probability that {0} wins: {1}".format(team2, 1 - prediction))
	else:
		print ("Probability that {0} wins: {1}".format(team1, prediction))

trainedModel = trainModel()
# # First round games in the South
# print("South:")
# findWinner('Virginia', 'UMBC', trainedModel)
# findWinner('Creighton', 'Kansas St', trainedModel)
# findWinner('Kentucky', 'Davidson', trainedModel)
# findWinner('Arizona', 'Buffalo', trainedModel)
# findWinner('Miami FL', 'Loyola-Chicago', trainedModel)
# findWinner('Tennessee', 'Wright St', trainedModel)
# findWinner('Nevada', 'Texas', trainedModel)
# findWinner('Cincinnati', 'Georgia St', trainedModel)
# # First round games in the East
# print("East:")
# findWinner('Villanova', 'Radford', trainedModel)
# findWinner('Virginia Tech', 'Alabama', trainedModel)
# findWinner('West Virginia', 'Murray St', trainedModel)
# findWinner('Wichita St', 'Marshall', trainedModel)
# findWinner('Florida', 'St Bonaventure', trainedModel)
# findWinner('Texas Tech', 'SF Austin', trainedModel)
# findWinner('Arkansas', 'Butler', trainedModel)
# findWinner('Purdue', 'CS Fullerton', trainedModel)
# # First round games in the West
# print("West:")
# findWinner('Xavier', 'TX Southern', trainedModel)
# findWinner('Missouri', 'Florida St', trainedModel)
# findWinner('Ohio St', 'S Dakota St', trainedModel)
# findWinner('Gonzaga', 'UNC Greensboro', trainedModel)
# findWinner('Houston', 'San Diego St', trainedModel)
# findWinner('Michigan', 'Montana', trainedModel)
# findWinner('Texas A&M', 'Providence', trainedModel)
# findWinner('North Carolina', 'Lipscomb', trainedModel)
# # First round games in the Midwest
# print("Midwest:")
# findWinner('Kansas', 'Penn', trainedModel)
# findWinner('Seton Hall', 'NC State', trainedModel)
# findWinner('Clemson', 'New Mexico St', trainedModel)
# findWinner('Auburn', 'Col Charleston', trainedModel)
# findWinner('TCU', 'Syracuse', trainedModel)
# findWinner('Michigan St', 'Bucknell', trainedModel)
# findWinner('Rhode Island', 'Oklahoma', trainedModel)
# findWinner('Duke', 'Iona', trainedModel)

findWinner('Virginia', 'Villanova', trainedModel)