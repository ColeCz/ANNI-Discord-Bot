import utils.helpers as helpers
import discord
from discord.ext import commands
import datetime
from datetime import timezone
from datetime import timedelta


class view(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	async def createLog(self, ctx) -> None:
		log = dict() #dictionary for members
		memData = dict() #dictionary for individual member data
		members = ctx.guild.members 
		nickName = str()
		memberName = str()
		
		#keywords
		internKeys = ["intern", "novice"]
		volunteerKeys = ["volunteer", "associate", "worker", "member"]
		leaderTokens = ["leader","manager"]

		#flag variables
		isLeader = bool(False)
		inTeam = bool(False)

		for member in members:
			if member.bot == False:
				nickName = member.nick
				if nickName:
					memberName = nickName
				else:
					memberName = member.global_name

				memData = {
					"id": member.id,
					"name": memberName,
					"startdate": member.joined_at,
					"enddate": "na",
					"birthday": "na",
					"team": "na",
					"teamleader": "na",
					"teamleaderid": "na",
					"position": "na"
				}
			    #beginning of block contains for loops that search individual member roles to set default variables.
				for role in member.roles:
				#check for roles regarding position in organization
					if str(role).lower() in internKeys:
						memData["position"] = "intern"
						period = timedelta(weeks=16)    #time period of internship
						join_date = member.joined_at    #date that member joined the server
						end_date = join_date + period #overload operator for datetime that returns timedelta obj
						memData["enddate"] = end_date
					elif str(role).lower() in volunteerKeys:
						memData["position"] = "volunteer"

					if "team" in str(role).lower() and "leader" not in str(role).lower():
						teamList = str(role).lower().split()
						memData["team"] = teamList[1] #Team name without the preceding 'team'
				
				#Block to find additional information based on above results
				if memData["team"] != "na":	#If the member has been assigned a team role
					for m in members:
						isLeader = False
						inTeam = False
						nickName = m.nick
						if nickName:
							memberName = nickName
						else:
							memberName = m.global_name

						for r in m.roles:
							for t in leaderTokens:
								if t in str(r).lower():
									isLeader = True
							if memData["team"].lower() in str(r).lower():
								inTeam = True
						
						if isLeader == True and inTeam == True:
							memData["teamleader"] = str(memberName)
							memData["teamleaderid"] = str(m.id)
							break
			    
			    #Add member dictionary to log dictionary
				log[member.id] = memData #set memdata to an element in the log dict()
				memData = dict() #reset memdata for next iteration in loop

		helpers.saveCache("MemberData","members.yaml", log)

	@commands.command(name="writecache", description="Save server member data.")
	async def writecache(self, ctx):
		try:
			await self.createLog(ctx)
			await ctx.send("I created and saved cache of server members.")
		except Exception as e:
			print("Error, unable to create log file [view::writecache]\n Exception: " + e)
			await ctx.send("Sorry, I was unable to write the log file.")

	@commands.command(name="memc", description="Alias to memberconfig command.")
	async def memc(self, ctx):
		await self.memberconfig(ctx)

	@commands.command()
	async def memberconfig(self, ctx):
		#check if member accessing function is an admin
		if helpers.checkAuth(ctx.author) == False:
			ctx.send("Sorry, you do not have authorization to use this command.")
			return #exit function

		#list acceptable token forms in order to interpret commands
		helpTokens = ["all", "print", "show", "questions", "quest", "help"]
		internTokens = ["intern", "internship","in"]
		volunteerTokens = ["vol", "volunteer", "worker", "employee"]
		trueTokens = ["yes", "true", "sure", "positive", "correct", "go", "on"]
		falseTokens = ["no", "false", "nope", "negative", "wrong", "stop", "off"]
		dateTokens = ["makedate", "date", "this", "thisdate", "now"]

		#runtime list objects
		allerrors = list()
		memberArgs = list()
		memberids = list()

		#runtime flag variables
		showHelp = bool(False)
		validField = bool(False)
		setEndDate = bool(False)

		#runtime variables
		newValue = None
		field = None

		#split message to tokens
		stripped = ctx.message.content.replace("[","").replace("]","")
		tokens = stripped.split()
		data = str()

		#get log from yaml config file
		log = helpers.loadCache("MemberData","members.yaml")
		if bool(log) == False: #check to see if the log is empty -- meaning it could not be loaded
			await self.createLog(ctx) #create new log
			log = helpers.loadConfig("members")
			if bool(log) == False:
				allerrors.append("Log file does not exist.")
				print("Error, log file does not exist [view::memberconfig]")

		if len(tokens) == 1:    #show help message if no arguments given
			showHelp = True

		elif len(tokens) == 2:  
			if tokens[1].isdigit() == False and tokens[1].lower() in helpTokens: #show help message if help argument given
				showHelp = True

		elif len(tokens) == 4:  #contains command name/id(s) field newValue
			if "," in tokens[1]:    #multiple members
				memberArgs = tokens[1].split(",")
			else:   #single member
				memberArgs.append(tokens[1])

			for mem in memberArgs:
				if mem.isdigit(): #find members based on index or id
					for i,member in enumerate(log.keys()):
						if int(mem) == int(member) or int(mem) == i:
							memberids.append(member)
				else: #find members based on name
					for member in log:
						if mem.lower() == log[member]["name"].lower():
							memberids.append(member)

			keyList = list(log.keys()) #convert dictionary view to list of keys
			if len(keyList) > 0:
				for f in log[keyList[0]].keys(): #iterate through member fields
					if tokens[2].lower() == f.lower():
						field = f #check if the given field argument is valid
						validField = True

				if validField == True:	#check if the field to modify exists
					newValue = tokens[3]

			else:
				allerrors.append("Log is empty.")
				print("Error, log empty as well as keyList [view::memberconfig]")

			#calculate change regarding the new value to be added. This ensures consistancy of values in log.
			if newValue is not None and validField == True and len(memberids) > 0: #checks to see if a new value and valid field were given
				if field.lower() == "position":
					if newValue in internTokens:
						newValue = "intern"
						setEndDate = True
					elif newValue in volunteerTokens:
						newValue = "volunteer"
					else:
						print("Error: invalid value given for intern status [view::memberconfig]")
						allerrors.append("Unable to interpret newValue for intern status.")
				elif field.lower() == "startdate" or field == "enddate":
					cur_date = datetime.datetime.now(timezone.utc)
					if newValue in dateTokens:
						newValue = cur_date
					elif "/" in newValue or "-" in newValue:
						newValue = helpers.convertTime(newValue)
					else:
						print("Error: invalid token for start date argument [view::memberconfig]")
						allerrors.append("Unable to interpret date argument.")
				elif field.lower() == "birthday":
					if newValue in dateTokens:
						newValue = datetime.datetime.now(timezone.utc)
					elif "/" in newValue or "-" in newValue:
						newValue = helpers.convertTime(newValue)
					else:
						print("Error: invalid token for birthday argument [view::memberconfig]")
						allerrors.append("Unable to interpret birthday date argument.")
				elif field.lower() == "citizen":
					if newValue in trueTokens:
						newValue = "true"
					elif newValue in falseTokens:
						newValue = "false"
					else:
						print("Error: invalid token for citizen argument [view::memberconfig]")
						allerrors.append("Unable to interpret new value token for citizenship.")
			else:
				print("Error: memberconfig command arguments are not valid [view::memberconfig]")
				data = "Sorry, it looks like your command has some arguments that I do not recognize or cannot find, use the !how command for help."

		if len(allerrors) == 0 and showHelp == False: #no errors at this point so proceed
			for m in memberids:
				log[m][field] = newValue #update log if parameters are valid
				if setEndDate == True: #intern field is being set which means enddate must be configured
					period = timedelta(weeks=16)
					join_date = log[m]["startdate"]
					end_date = join_date + period #overload operator for datetime that returns timedelta obj
					log[m]["enddate"] = end_date
				
			try:	#save new member config to file
				helpers.saveCache("MemberData", "members.yaml", log) #save modified config file
				print("Successfully saved config file [view::memberconfig]")
			except:
				print("Error: could not save new config [view::memberconfig]")
				allerrors.append("Unable to save configuration.")

		if len(allerrors) == 0 and showHelp == False:
			data = "I successfully updated my member data!"
		elif len(allerrors) == 0 and showHelp == True:
			data = "SYNTAX: !memberconfig [name/id] [field] [new value]"
		else:
			data = "Sorry, I was unable to interpret your command. Use `!how` for help.\n"
			data = data + "**Errors:**\n"
			for e in allerrors:
				data = data + "- **[E] ->** " + e + "\n"

		await ctx.send(data)    #send message created above to the discord chat the command was sent from


	@commands.command(name="view", description="View bot member data.")
	async def view(self, ctx) -> None:
		#check if member accessing function is an admin
		if helpers.checkAuth(ctx.author) == False:
			await ctx.send("Sorry, you do not have authorization to use this command.")
			return #exit function

		#convert bot command to token list
		stripped = ctx.message.content.replace("[","").replace("]","")
		tokens = stripped.split()
		data = str()
		errors = list()

		#runtime flag variables
		filterSearch = bool(False)
		allMembers = bool(False)
		viewFields = bool(False)
		
		#runtime variables
		field = str()
		searchWord = str()
		keyList = list()


		#get log from yaml config file
		log = helpers.loadCache("MemberData","members.yaml")
		if bool(log) == False: #check to see if the log is empty -- meaning it could not be loaded
			await self.createLog(ctx) #create new log
			log = helpers.loadCache("MemberData","members.yaml")
			if bool(log) == False:
				errors.append("Unable to load members from log.")


		#log variables
		keyList = list(log.keys())
		fields = list(log[keyList[0]].keys())


		if len(tokens) == 3:
			for i in fields:
				if tokens[1] == i:
					field = str(tokens[1]).lower()
					if tokens[2].isdigit():
						searchWord = tokens[2]
					else:
						searchWord = tokens[2].lower()
					filterSearch = True

		elif len(tokens) == 2:
			if tokens[1] == "all":
				allMembers = True
			elif tokens[1] == "fields" or tokens[1] == "help":
				viewFields = True
			else:
				errors.append("Unknown command option used.")
				print("Error, invalid option used with view [view::view]")

		elif len(tokens) == 1:
			errors.append('''Using view without arguments is disabled to prevent output 
				 overload. To view all data: `!view all`''')

		else:
			errors.append("Invalid arguments or improper arguments used.")
			print("Error: Invalid arguments given [view::view]")
			

		if allMembers == True: #create a list of all data in log
			for i,member in enumerate(log):
				data = data + "**Member " + str(i) + ":**\n"
				for field in log[member].keys():
					data = data + "  " + str(field) + "  :  " + str(log[member][field]) + "\n"
				data = data + "\n\n"

		elif filterSearch == True: #create a list of data containing searched fields
			for i,member in enumerate(log):
				if str(log[member][field]).lower() == str(searchWord):
					data = data + "**Member: " + str(log[member]["name"]) + "**\n"
					for field in log[member].keys():
						data = data + "  " + str(field) + "  :  " + str(log[member][field]) + "\n"
					data = data + "\n\n"
			if len(data) < 1:
				errors.append("There are no results matching this search.")

		elif viewFields == True:
			data = "**Search fields:**\n"
			for f in fields:
				data = data + "- " + f + "\n"
			data = data + "\nEnter !view [field] [search value]"
		
		else:
			errors.append("Unable to interpret command arguments.")

		
		if len(data) < 1 or len(errors) > 0:
			data = "Sorry, I am not able to fullfill your command, use the `!how` command for help.\n\n"
			data = data + "**Errors: **\n"
			for e in errors:
				data = data + "- **[E] ->** " + e + "\n"
			await ctx.send(data)
		else:
			await ctx.send(data)


	@commands.command(name="get", description="Get data lists from bot.")
	async def get(self, ctx) -> None:
		stripped = ctx.message.content.replace("[","").replace("]","")
		tokens = stripped.split()
		data = str()
		errors = list()

		#get log from yaml config file
		log = helpers.loadCache("MemberData","members.yaml")
		if bool(log) == False: #check to see if the log is empty -- meaning it could not be loaded
			await self.createLog(ctx) #create new log
			log = helpers.loadCache("MemberData","members.yaml")
			if bool(log) == False:
				errors.append("Unable to load members from log.")


		if len(tokens) == 2: #command with one argument
			if tokens[1] == "interns" or tokens[1] == "intern":
				data = "Interns: \n\n"
				for member in log:
					if log[member]["position"] == "intern":
						data = data + log[member]["name"] + "\n"
			else:
				errors.append("Invalid argument to command.")
		else:
			errors.append("Invalid number of arguments given.")

		if len(data) < 1 or len(errors) > 0:
			data = "Sorry, I am not able to fullfill your command, use the `!how` command for help.\n"
			data = data + "**Errors: **\n"
			for e in errors:
				data = data + "- **[E] ->** " + e + "\n"
			await ctx.send(data)
		else:
			await ctx.send(data)
		
		
async def setup(bot):
	await bot.add_cog(view(bot))
