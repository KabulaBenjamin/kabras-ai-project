@echo off 
REM Kabras AI Project Setup 
mkdir kabras-ai-project 
cd kabras-ai-project 
mkdir data data\raw data\processed data\synthetic 
mkdir lexicon 
mkdir models models\base models\fine_tuned models\checkpoints 
mkdir notebooks 
mkdir app app\android 
mkdir reports 
echo { > lexicon\kabras_lexicon.json 
echo   "phrases": [ >> lexicon\kabras_lexicon.json 
echo     {"kabras": "Mulembe", "english": "Hello"}, >> lexicon\kabras_lexicon.json 
echo     {"kabras": "Omusana niwanga", "english": "The sun is hot today"}, >> lexicon\kabras_lexicon.json 
echo     {"kabras": "Uli wapi?", "english": "Where are you going?"} >> lexicon\kabras_lexicon.json 
echo   ] >> lexicon\kabras_lexicon.json 
echo } >> lexicon\kabras_lexicon.json 
