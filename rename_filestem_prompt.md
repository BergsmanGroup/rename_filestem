I want you to create a small application that will rename filestems in a directory. This is used to systematically rename many files of datasets that use identical and/or related filestems.

It should have a small gui with a browse feature to select either an entire directory or a subset of individual files. Can this be one button?

When selecting a directory, or if a subdirectory is selected alongside files at the top level, if there are matching file stems in any subdirectories, these should be selected alongside the top level files. 

The following find/replace behavior should allow the user to act on all the files within all the directories selected and allow for a granular selection of subdirectories. There should be a dropdown button for "Active Directory" with the default selection set to "all" and the other options set to the list of the parent directory and all relevant sub directories.

We will start with just one mode of find/replace behavior but prepare the infrastructure for allow for other methods of file name normalization.
1. Find/replace exact string in-line without changing the rest of the text in the given file name. If a full filename is given, this will produce only files with that exact name (multiplied by however many formats that file exists in ie .dat .txt and .se)

Below the directory selection field, there will be s find text fields which should be able to autofill text based on the contents of the parent directory and its sub directories. There will also be a replace text field which should likewise be able to autofill text. Create a config file with settings for these autofill behaviors. Default "find" to autofill and default "replace" to not autofill. 

Below the text fields, there should be a "Find" button. When this is pressed, all matching files should be found. The drop down for "active directory" should be next to the find button, it should be a nested drop down like that in "directory nesting.png". This should only show the directory names and imply their relative paths from the nesting behavior, allowing for the select all/select none/select one behavior that is seen in the image. After finding all matching files, this drop down can be populated according to which directories contain matching files. There should also be a replace button in this row. 

Below these controls, there should be a selection window like that of "selection behavior.png" in this workspace that allows files to be selected from the list of matched files in that directory / directory level. 