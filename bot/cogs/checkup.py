#Imports
import utils.helpers as helpers
import os.path
from datetime import datetime, timezone

#Discord imports
import discord
from discord.ext import commands

#Scheduler imports
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

#Google imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class checkup(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		# Create an instance of the scheduler
		self.scheduler = AsyncIOScheduler()
		self.scheduled = bool(False)
		self.taskNum = int(0)
		self.context = None
		# Scheduler variables
		self.scheduler.start()
		self.reportedMembers = list()
		self.unreportedMembers = list()
		# Google API variables
		self.creds = None

		print("IMPORTANT SETUP: Run `!setup` command in server to set up intern reminder feature!")
		print("IMPORTANT SETUP: Add Google Form link with `!replink` command")
	

	def getReportedMembers(self) -> list: #get a list of members that submitted a Google Form Report
		CONF = helpers.loadConfig("GoogleSheetAPI.yaml") #Get config for API
		ID = helpers.loadConfig("GoogleSheetID.yaml") #Get id of google sheet that holds intern responses
		SCOPES = CONF["SCOPE"]
		SPREADSHEET_ID = ID["SPREADSHEET_ID"]
		RANGE_NAME = "Form Responses 1" #Add range of !'first cell':'last cell'
		NAMEINDEX = CONF["NAMEINDEX"]
		TIMEINDEX = CONF["TIMEINDEX"]
		CUTOFFAGE = CONF["CUTOFFAGE"]

		reportedMembers = list()
		today = datetime.now(timezone.utc)

		if os.path.exists("cache/GoogleAPI/token.json"):
			self.creds = Credentials.from_authorized_user_file("cache/GoogleAPI/token.json", SCOPES)

		# If there are no (valid) credentials available, let the user log in.
		if not self.creds or not self.creds.valid:
			if self.creds and self.creds.expired and self.creds.refresh_token:
				self.creds.refresh(Request())
			else:
				flow = InstalledAppFlow.from_client_secrets_file(
				"cache/GoogleAPI/credentials.json", SCOPES
				)
			self.creds = flow.run_local_server(port=0)
		# Save the credentials for the next run
		with open("cache/GoogleAPI/token.json", "w") as token:
			token.write(self.creds.to_json())
		
		try:
			service = build("sheets", "v4", credentials=self.creds)

			# Call the Sheets API
			sheet = service.spreadsheets()
			result = (
				sheet.values()
				.get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME)
				.execute()
			)
			values = result.get("values", [])

			if not values:
				print("Error, could not retrieve data from Google Sheets.")
				return

			values.pop(0) #remove first entry in response list - column title
			#Save names of members in report
			for row in reversed(values): #Reverse values so newest entries are at the beginning
				try:
					responseDate = datetime.strptime(str(row[TIMEINDEX]), "%m/%d/%Y %H:%M:%S").replace(tzinfo=timezone.utc)
					responseAge = today - responseDate
					if responseAge.days < CUTOFFAGE: #only add responses that are less than four days old
						reportedMembers.append(str(row[NAMEINDEX]))
					else:
						break #Since entries are in order of newest to oldest, an old entry breaks the loop
				except Exception as e:
					print("Error, invalid time format in response sheet. [checkup::getReportedMembers]\n Exception: " + str(e))	
					return

		except HttpError as e:
			print("Error, Http Error encountered[checkup::getReportedMembers]:\n Exception: " + str(e))

		#Return list of member names from report
		return reportedMembers


	async def checkMissedSubmissions(self) -> None:
		link = helpers.loadCache("GoogleAPI", "FormLink.yaml") #get google form link from yaml file.
		if link["formlink"] is not None or link["formlink"] != "" and self.creds is not None:
			data = str()
			try:
				members = self.context.guild.members
			except Exception as e:
				print("Error, ctx member has not been saved! [checkup::checkMissedSubmissions]\n Exception: " + e)
			log = helpers.loadCache("MemberData","members.yaml")
			teams = dict()

			#Get team leaders and create team keys with their names
			for member in members:
				for role in member.roles:
					if "leader" in str(role) or "manager" in str(role):
						teams[member.id] = dict()
						teams[member.id]["reported"] = list()
						teams[member.id]["noreport"] = list()
			#Get team members and add them to list values according to team leader keys
			for member in log:
				for leader in teams:
					if log[member]["teamleaderid"] == str(leader) and log[member]["position"] == "intern":
						if log[member]["name"] in self.reportedMembers:
							teams[leader]["reported"].append(log[member]["name"])
						elif log[member]["name"] in self.unreportedMembers:
							teams[leader]["noreport"].append(log[member]["name"])
						else:
							print("ALERT: server intern not accounted for in progress reports: "+str(log[member]["name"])+" [checkup::checkMissedSubmissions]")
			
			#Save teams data to a cache file at /cache/InternSubmissionLog/ with today's date as file name
			today = str(datetime.today())
			dateAndTime = today.split()
			helpers.saveCache("InternSubmissionLog", str(dateAndTime[0]) + ".yaml", teams)

			#Create and send messages to leaders regarding intern form submissions
			for leader in teams:
				data = str()
				data = "**Interns that did not submit a report this week:**\n"
				for intern in teams[leader]["noreport"]:
					data = data + " " + str(intern) + "\n"
				data = data + "**Inters that submitted a report:**\n"
				for intern in teams[leader]["reported"]:
					data = data + " " + str(intern) + "\n"

				for m in members:
					if str(m.id) == str(leader):
						await m.send(data)
		else:
			print("Error, Google Form link or API credentials are missing. [checkup::checkMissedSubmissions]")

	async def checkSubmissions(self) -> None:
		link = helpers.loadCache("GoogleAPI", "FormLink.yaml") #get google form link from yaml file.
		if link["formlink"] is not None or link["formlink"] != "" and self.creds is not None:
			data = str()
			members = self.context.guild.members
			log = helpers.loadCache("MemberData","members.yaml")
			link = helpers.loadCache("GoogleAPI", "FormLink.yaml")
			self.reportedMembers = self.getReportedMembers()
			self.unreportedMembers = list()
			
			for m in log:
				if log[m]["position"].lower() == "intern" and log[m]["enddate"] > log[m]["startdate"] and log[m]["name"] not in self.reportedMembers:
					self.unreportedMembers.append(log[m]["name"])
					data = "Hey there, I hope your week has been going well! "
					data = data + "Don't forget to submit your weekly report for your team leader!\n"
					data = data + "Enter your weekly report here: " + link["formlink"] + "\n"
					if log[m]["teamleader"] != None and log[m]["teamleader"] != "na":
						data = data + "Your team leader is " + log[m]["teamleader"]
					
					for member in members:
						if member.id == m:
							await member.send(data)
		else:
			print("Error, Google Form link or API credentials are missing. [checkup::checkSubmissions]")

		
	@commands.command(name = "runcheck", description = "runs the checkup reminder for interns")
	async def runcheck(self, ctx) -> None:
		self.context = ctx #set member to current ctx
		data = str()
		#check authorization
		authorized = helpers.checkAuth(ctx.author)

		if authorized == True:
			data = "Sent progress update reminders to interns!"
			await self.checkSubmissions()
		else:
			data = "Sorry, you do not have authorization to run this command."
			
		await ctx.send(data)

	@commands.command(name = "schedule", description = "Schedules intern reminders for a specific time and date")
	async def schedule(self, ctx) -> None:
		self.context = ctx #update member to current ctx
		data = str()
		errors = list()
		authorized = helpers.checkAuth(ctx.author) #check authorization
		stripped = ctx.message.content.replace("[","").replace("]","") #remove brackets from command string
		tokens = stripped.split() #split command string into list of words
		jobs = self.scheduler.get_jobs()
		
		#constant keywords
		shortDays = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
		days = {
			"monday": "mon",
			"tuesday": "tue",
			"wednesday": "wed",
			"thursday": "thu",
			"friday": "fri",
			"saturday": "sat",
			"sunday": "sun"
		}
		remove = ["rm", "remove", "r"]
		show = ["all", "show", "help", "list"]
		
		#temp variables
		d = None #day
		h = None #hour
		m = None #minute
		jobIndex = None #Job index from job list
		checkMissedTokens = ["note", "notify"]
		checkSubmissionsTokens = ["rem", "remind"]
		
		#flag variables
		mkschedule = bool(False)
		removeSchedule = bool(False)
		showAll = bool(False)
		scheduleMissedSubmisions = bool(False)
		scheduleInternReminder = bool(False)
		
		if authorized == True:
			#Iterate through tokens to set flag variables used to determine output
			for token in tokens:
				if token.lower() in show:
					showAll = True
				elif token.lower() in checkMissedTokens:
					scheduleMissedSubmisions = True
					mkschedule = True
				elif token.lower() in checkSubmissionsTokens:
					scheduleInternReminder = True
					mkschedule = True
				elif token.lower() in days:
					d = days[token.lower()]
				elif token.lower() in shortDays:
					d = token.lower()
				elif token.lower() in remove:
					removeSchedule = True
				elif token.isdigit():
					jobIndex = int(token)

				elif ":" in token and mkschedule == True:
					timeFields = token.split(":")
					if len(timeFields) == 2:
						h = int(timeFields[0])
						m = int(timeFields[1])
					else:
						errors.append("Too many or too little time fields. Use HH:MM")
						print("Error, Invalid # of time fields [checkup::schedule]")
			
			if len(tokens) == 1:
				showAll = True

			#Use flag variables to create output
			if showAll == True:
				for job in jobs:
					data = data + f"Job ID: {job.id}\n"
					data = data + f"Job Name: {job.name}\n"
					data = data + f"Next Run Time: {job.next_run_time}\n"
					data = data + f"Trigger: {job.trigger}\n"
					data = data + "---\n"
				if len(data) < 1:
					data = "It looks like there are no jobs to view."
			
			elif removeSchedule == True and jobIndex is not None:
				try:
					self.scheduler.remove_job(str(jobIndex))
					data = "Done!"
				except Exception as e:
					errors.append("Unable to remove job do to an error.")
					print("Error, unable to remove job from scheduler [checkup::schedule]\n Exception: " + e)
			elif scheduleInternReminder == True and d is not None and h is not None and m is not None:
				self.taskNum = self.taskNum + 1
				try:
					self.scheduler.add_job(self.checkSubmissions, 
						CronTrigger(day_of_week = d, hour = h, minute = m, second = 0),
						id = str(self.taskNum),
						name = "Scheduled job for checkup.checkSubmissions",
						replace_existing = True
					)
					data = "Done!"
				except Exception as e:
					print("Error, unable to schedule intern reminder task [checkup:schedulecheck]\n Exception: " + e)
					errors.append("Sorry, I was not able to schedule an intern reminder task.")
			elif scheduleMissedSubmisions == True and d is not None and h is not None and m is not None:
				self.taskNum = self.taskNum + 1
				try:
					self.scheduler.add_job(self.checkMissedSubmissions, 
						CronTrigger(day_of_week = d, hour = h, minute = m, second = 0),
						id = str(self.taskNum),
						name = "Scheduled job for checkup.checkMissedSubmissions",
						replace_existing = True
					)
					data = "Done!"
				except Exception as e:
					print("Error, unable to schedule missed submission task [checkup:schedulecheck]\n Exception: " + e)
					errors.append("Sorry, I was not able to schedule an missed submission task.")

		else: #else statement for authorization check
			errors.append("Sorry, you do not have authorization to run this command.")
			
		if len(data) > 1 and len(errors) == 0:
			await ctx.send(data)
		else:
			data = "Sorry, I was unable to complete your command. Use the `!how` command for help.\n"
			for e in errors:
				data = data + "**[E] ->** " + e + "\n"
			await ctx.send(data)


	@commands.command(name = "updatecheckup", description = "Update ctx member.")
	async def updatecheckup(self, ctx) -> None:
		self.context = ctx

	@commands.command(name = "setup", description = "Update ctx member and schedule reminders for interns.")
	async def setup(self, ctx) -> None:
		errors = list()
		data = str()
		self.context = ctx

		if self.taskNum < 2: #default jobs have not been created yet(verify first run)
			try:
				#schedule intern reminder for Friday at 5PM
				self.taskNum += 1
				self.scheduler.add_job(self.checkSubmissions, 
					CronTrigger(day_of_week = "sat", hour = 13, minute = 0, second = 0),
					id = str(self.taskNum),
					name = "Scheduled job for checkup.checkSubmissions",
					replace_existing = True
				)
				#schedule intern reminder for Saturday at 5PM
				self.taskNum += 1
				self.scheduler.add_job(self.checkSubmissions, 
					CronTrigger(day_of_week = "fri", hour = 17, minute = 0, second = 0),
					id = str(self.taskNum),
					name = "Scheduled job for checkup.checkSubmissions",
					replace_existing = True
				)
				#schedule check for missed intern submissions on Sunday at 9PM
				self.taskNum += 1
				self.scheduler.add_job(self.checkMissedSubmissions, 
					CronTrigger(day_of_week = "sat", hour = 17, minute = 0, second = 0),
					id = str(self.taskNum),
					name = "Scheduled job for checkup.checkMissedSubmissions",
					replace_existing = True
				)
				data = "Done! Default intern reminders for Friday and Saturday at 5PM EST have been set!"
			except Exception as e:
				print("Error, unable to schedule task [checkup:schedulecheck]\n Exception: " + e)
				errors.append("Sorry, I was not able to schedule the task.")
		else:
			data = "Updated context for intern reminder feature!"

		if len(errors) > 0 or data == "":
			data = "Sorry something went wrong. Use the `!how` command for help.\n**Errors:**\n"
			for e in errors:
				data = data + "**[E] -> ** " + e + "\n" 
			await ctx.send(data)
		else:
			await ctx.send(data)
		
	
	@commands.command(name = "testapi", description = "Run a test on the Google Sheets API.")
	async def testapi(self, ctx) -> None:
		members = list()
		data = str()
		authorized = helpers.checkAuth(ctx.author) #check authorization

		if authorized == True:
			try:
				members = self.getReportedMembers()
				data = "Success, the API is fully functional!\n"
				data = data + "Entries in Google Sheet: " + str(len(members))
				data = data + "\n\n" + str(members)
			except Exception as e:
				print("Error, Google Sheets API test failed [checkup::testapi]\n Exception: " + str(e))
				data = "Sorry, I was not able to get a response from the Google Sheets API."
		else:
			data = "Sorry, you are not authorized to use this command."

		await ctx.send(data)

	@commands.command(name = "testinterncheckup", description = "Run a test on the Google Sheets API.")
	async def testinterncheckup(self, ctx) -> None: #ONLY TO BE USED FOR DEBUGGING
		authorized = helpers.checkAuth(ctx.author) #check authorization

		if authorized == True:
			await self.checkSubmissions() #Check and send reminders to interns
			await self.checkMissedSubmissions() #Check which interns missed their submissions
		else:
			await ctx.send("Sorry, you are not authorized to run this command")


	@commands.command(name = "replink", description = "Update Google Form report link.")
	async def replink(self, ctx) -> None:
		stripped = ctx.message.content.replace("[","").replace("]","")
		tokens = stripped.split()
		data = str()
		link = {"formlink": None}
		errors = list()

		if len(tokens) == 2:
			link["formlink"] = tokens[1]
			helpers.saveCache("GoogleAPI", "FormLink.yaml", link)
			data = "Done, saved " + tokens[1] + " as the new Google Form report link."
		else:
			errors.append("Invalid number of arguments used.")
		
		if len(data) < 1 or len(errors) > 0:
			data = "Sorry, I am not able to fullfill your command, use the !how command for help.\n"
			data = data + "Errors: \n"
			for e in errors:
				data = data + "[E] " + e + "\n"
			await ctx.send(data)
		else:
			await ctx.send(data)

	@commands.command(name = "form", description = "Get intern progress update Google Form link.")
	async def form(self, ctx) -> None:
		data = str()
		link = dict()

		try:
			link = helpers.loadCache("GoogleAPI", "FormLink.yaml")
			data = "Send your progress update here: " + str(link["formlink"])
			await ctx.send(data)
		except Exception as e:
			data = "Sorry, the Google Form link has not been added or there was an error."
			print("Error, Unable to access Google Form link [checkup::form]\n Exception: " + str(e))
			await ctx.send(data)

async def setup(bot):
	await bot.add_cog(checkup(bot))
