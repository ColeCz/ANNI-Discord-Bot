from utils.helpers import loadCache, getTimeStamp
from discord.ext import commands
from datetime import tzinfo, timedelta, datetime, timezone

MEMBER_DATA_DIR_NAME = "MemberData"
MEMBER_DATA_FILE_NAME = "members.yaml"

INTERNSHIP_END_QUESTION = '1'
TEAM_QUESTION = '2'
MODERATORS_QUESTION = '3'
TEAM_LEADS_QUESTION = '4'

class chatbot(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name="ask", description="ask the bot a question")
	async def ask(self, ctx) -> None:
		#get the discord server's member data from the yaml config file cache
		member_data = loadCache(MEMBER_DATA_DIR_NAME, MEMBER_DATA_FILE_NAME)
		
		try:
			author_stats=member_data[ctx.author.id]
		except Exception as e:
			print(str(e))

		#Token bank to decifer commands
		questions = {
            INTERNSHIP_END_QUESTION: "When does my internship end?",
            TEAM_QUESTION: "What team am I part of?",
            MODERATORS_QUESTION: "Who are the moderators?",
            TEAM_LEADS_QUESTION: "Who are my team leaders?"
        }
		stripped = ctx.message.content.replace("[","").replace("]","")
		tokens = stripped.split()
		
		#command interpretation per token(word)
		if len(tokens) < 2:
			bot_message = "**Enter `!ask` + the number representing the question you wish to ask!**\n"
			bot_message += "\n".join(f"{key}: {question}" for key, question in questions.items())
			await ctx.send(bot_message)
			return
		
		question_id = tokens[1]

		if question_id == INTERNSHIP_END_QUESTION:
			if author_stats["position"].lower() == "intern":
				join_date = author_stats["startdate"]
				cur_date = datetime.now(timezone.utc)
				end_date = author_stats["enddate"]
				joinStamp = getTimeStamp(join_date)
				endStamp = getTimeStamp(end_date)
				time_until_end = end_date - cur_date
				if cur_date < end_date:
					bot_message = "You joined " + str(joinStamp) + " and your intership ends " + str(endStamp) + "." + "\n" + "You have " + str(int(time_till_end.days / 7)) + " weeks and " + str(time_till_end.days % 7) + " days left."
				else:
					bot_message = "Your internship ended " + str(endStamp)
			else:
				bot_message = "It appears that you do not have an end date as you are not an intern."
			
			await ctx.send(bot_message)
			return
		elif question_id == TEAM_QUESTION:
			team_roles = [role.name for role in ctx.author.roles if "team" in role.name.lower()]
			if team_roles:
				bot_message = "Your team in this server:\n" + "\n".join(team_roles)
			else:
				bot_message = "Sorry, I was not able to determine your team."

			await ctx.send(bot_message)
			return
		elif question_id == MODERATORS_QUESTION:
			moderators = [member.global_name for member in ctx.guild.members if any("moderat" in role.name.lower() for role in member.roles)]
			if moderators:
				bot_message = "The server moderators are:\n" + "\n".join(moderators)
			else:
				bot_message = "Sorry, I was unable to find the moderators."

			await ctx.send(bot_message)
			return
		elif question_id == TEAM_LEADS_QUESTION:
			team_leader = author_stats.get("teamleader", "na")
			if team_leader != "na":
				bot_message = f"Your team leader is: {team_leader}"
			else:
				bot_message = "Sorry, I am unable to find your team leader."

			await ctx.send(bot_message)
			return		
		
		# default case
		print("Error: invalid question [chatbot::ask]")	
		bot_message = "Sorry, I was not able to interpret this command. Please use the !how command for help."

		await ctx.send(bot_message)

async def setup(bot):
	await bot.add_cog(chatbot(bot))
