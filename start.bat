@start py nodeserver.py conf1_idofront.yml
@start py nodeserver.py conf2_orth.yml
@echo Nodes Launched
@pause
@start test.py mine 1120
@echo Miner started
@pause
@start test.py simutx 1120
@start test.py simutx 1121