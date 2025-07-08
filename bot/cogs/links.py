import utils.helpers as helpers
import discord
from discord.ext import commands
import datetime
from datetime import timezone

'''
Commands:

meet! -> "Meeting is starting now! [link]"



'''


class time(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name="link", description="save, remove, view links")
	async def link(self, ctx):
		stripped = ctx.message.content.replace("[","").replace("]","")
		tokens = stripped.split()
		data = str()

		#flag variables
		remove = bool(False)
		save = bool(False)
		all = bool(False)
		
		# set flag variables for save or remove
		if len(tokens) >= 2:
			if tokens[1] == "remove" or tokens[1] == "rm" or tokens[1] == "delete":
				remove = True
			if tokens[1] == "save" or tokens[1] == "make" or tokens[1] =="add":
				save = True
			if tokens[1] == "all" or tokens[1] == "show" or tokens[1] == "list":
				all = True
		else:
			all = True


		#Logic for saving a link
		if save == True:
			if len(tokens) == 4:
				try:
					linkLog = helpers.loadCache("Links", "log.yaml")
				except:
					linkLog = dict()
				
				linkLog[tokens[2]] = tokens[3]
				try:
					helpers.saveCache("Links", "log.yaml", linkLog)
					data = "Done!"
					await ctx.send(data)
					return
				except:
					print("Error, Unable to save links [time::savelink]")
					data = "Sorry, I was not able to save this link."
					await ctx.send(data)
					return
			else:
				await ctx.send("I could not interpret your command. Use '!how' for help.\nCommand example: !savelink [name] [link]")
				return
			
		#Logic to show all links
		elif all == True:
			try:
				linkLog = helpers.loadCache("Links", "log.yaml")
				data = "**Links: **\n"
				for key in list(linkLog.keys()):
					data = data + "- " + key + " : " + linkLog[key] + "\n"

				data = data + "\n**Save new link:** !link save [name] [URL]\n"
				data = data + "**Remove saved link:** !link remove [name]\n"
				await ctx.send(data)
				return
			except Exception as e:
				print("Error, unable to load cache file [time::link]\n Exception: " + e)
				data = "Sorry, I was unable to retrieve the links."
				await ctx.send(data)
				return
			
		elif remove == True:
			if len(tokens) == 3:
				try:
					linkLog = helpers.loadCache("Links", "log.yaml")
				except Exception as e:
					print("Error: Unable to read links [time::link]\n Exception: " + e)
					await ctx.send("No need to delete. There are no links saved.")
					return

				if tokens[2] in list(linkLog.keys()):
					del linkLog[tokens[2]]
					try:
						helpers.saveCache("Links", "log.yaml", linkLog)
						data = str(tokens[2]) + " has been deleted."
						await ctx.send(data)
						return
					except Exception as e:
						print("Error, unable to save cache file [time::link]\n Exception: " + e)
						await ctx.send("I was unable to delete that link.")
						return
				else:
					data = "Sorry, I do not have a link associated with " + tokens[2]
					await ctx.send(data)
					return
			else:
				data = "Sorry, I was unable to interpret your command. Use the '!how' command for help."
				await ctx.send(data)
				return
		else:
			await ctx.send("It was not specified to save or remove this alias. Use the '!how' command for help.")
			return
	
	@commands.command(name="al", description="alias to alert command")
	async def al(self, ctx):
		await self.alert(ctx)
		
	@commands.command(name="meet", description="creates an alert")
	async def alert(self, ctx):

		# ensure sender has the correct permissions (NOTE blocks me out, but I can't test with a priveleged account)
		# if not helpers.checkAuth(ctx.author):
		# 	await ctx.send("You must be a manager to send the meeting link!")
		# 	return

		time_found = bool() # indicates if the command includes a time
		recipients = str("everyone") # who is mentioned in the chat when the response is sent
		tokens = list() # the command when separated by spaces
		data = str() # message that will be sent as response to command
		additional_data = list() # if the message includes extraneous data, we copy that into a clean array with no commands
		linkLog = helpers.loadCache("Links", "log.yaml") # load links from the yaml file
		gotLink = bool(False)
		minutes_until_meeting = bool(False) 
		link = str()
		default_link = str()

		if "default_link" in linkLog.keys():
			default_link = str(linkLog["default_link"])
		else: 
			default_link= str("https://us02web.zoom.us/j/89258513813?pwd=DIcmLw5SJzCaJxWssxX2vW2WBaywxj.1")

		stripped = ctx.message.content.replace("[","").replace("]","")
		tokens = stripped.split()
		
		if len(tokens) == 1: # if the user only enters "!meet", then we say the meeting is starting now and share the default link
			data = f"@{recipients} Meeting is starting now! [{default_link}]"
			await ctx.send(data)
			return
			
		else: # else we iterate the tokens and set the flags and values above
			for i, token in enumerate(tokens):
				for key in list(linkLog.keys()):
					if str(key).lower() == token:
						gotLink = True
						link = linkLog[key]
				
				if token.isdigit() == True and time_found == False:
					time_found = True
					minutes_until_meeting = int(token)
				
				if "$" in token:
					recipients = token.replace("$", "")

				if "%" in token:
					index = tokens.index(token)  # Get the index of the first token with '%', then copy all following tokens to new array
					additional_data = [tokens[index].lstrip('%')] + tokens[index + 1:]
		
		if time_found == True:

			data = data + "@" + recipients + " Meeting will be starting in " + str(minutes_until_meeting) + " minutes!"

			if gotLink == True:
				data = data + " [" + link + "]"
			else:
				data = data + " [" + default_link + "]"

		elif gotLink == True:
			data = data + "@" + recipients + " Our meeting is starting! " + link

		else:
			data = data + "@" + recipients + " Our meeting is starting! " + default_link

		data = data + "\n" + " ".join(additional_data)
		await ctx.send(data)
			

async def setup(bot):
	await bot.add_cog(time(bot))