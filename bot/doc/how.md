### COG: help
### NAME: how

**DESCRIPTION**:\
This command gives quick command information
as well as full documentation. It can be used to
get a 'copy and paste' command that a user can use
to interact with ANNI.

**USAGE**:\
- Running this command with no arguments will return
a list of options for the user:\
`!how`
	
- Adding the index of an option along with the command
will return another command that the user can then copy and paste:\
`!how 1` -> `!alert [link name]`\
This is becaues the first prompt for how is to send a meeting alert.
(See 'alert' documentation for information on alerts.)

- Any fields of the given command that are surrounded in square
brackets is a field that the user must fill in. For example, if a 
command includes: [day], the user should replace 'day' with the name
of the day they want to use. Such as [friday] or [monday].
