-- DO NOT WRITE CODE OUTSIDE OF THE if-then-end SECTIONS BELOW!! (unless the code is a function definition)

if (sim_call_type==sim_childscriptcall_initialization) then

	-- Put some initialization code here

	-- Make sure you read the section on "Accessing general-type objects programmatically"
	-- For instance, if you wish to retrieve the handle of a scene object, use following instruction:
	--
	-- handle=simGetObjectHandle('sceneObjectName')
	--
	-- Above instruction retrieves the handle of 'sceneObjectName' if this script's name has no '#' in it
	--
	-- If this script's name contains a '#' (e.g. 'someName#4'), then above instruction retrieves the handle of object 'sceneObjectName#4'
	-- This mechanism of handle retrieval is very convenient, since you don't need to adjust any code when a model is duplicated!
	-- So if the script's name (or rather the name of the object associated with this script) is:
	--
	-- 'someName', then the handle of 'sceneObjectName' is retrieved
	-- 'someName#0', then the handle of 'sceneObjectName#0' is retrieved
	-- 'someName#1', then the handle of 'sceneObjectName#1' is retrieved
	-- ...
	--
	-- If you always want to retrieve the same object's handle, no matter what, specify its full name, including a '#':
	--
	-- handle=simGetObjectHandle('sceneObjectName#') always retrieves the handle of object 'sceneObjectName'
	-- handle=simGetObjectHandle('sceneObjectName#0') always retrieves the handle of object 'sceneObjectName#0'
	-- handle=simGetObjectHandle('sceneObjectName#1') always retrieves the handle of object 'sceneObjectName#1'
	-- ...
	--
	-- Refer also to simGetCollisionhandle, simGetDistanceHandle, simGetIkGroupHandle, etc.
	--
	-- Following 2 instructions might also be useful: simGetNameSuffix and simSetNameSuffix

end


if (sim_call_type==sim_childscriptcall_actuation) then

	-- Put your main ACTUATION code here

	-- For example:
	--
	-- local position=simGetObjectPosition(handle,-1)
	-- position[1]=position[1]+0.001
	-- simSetObjectPosition(handle,-1,position)

	luacode = simGetStringSignal('my_lua_code')
	if (luacode) then
		f = loadstring(luacode)
		f()
		simClearStringSignal('my_lua_code')
  end
end


if (sim_call_type==sim_childscriptcall_sensing) then

	-- Put your main SENSING code here

end


if (sim_call_type==sim_childscriptcall_cleanup) then

	-- Put some restoration code here

end
