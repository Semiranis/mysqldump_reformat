# coding=UTF-8
"""
Script to split enormously long lines made by mysqldump into shorter lines.

"Extended insert" can create lines too long, making importing dump not
possible and resulting in "fake" errors (file is correct, but db engine reads
only as big part of the line as possible and tries to process it, omitting
the other part, frequently braking words or instructions in the middle).
It can be a problem if you can't make new dump without extended inserts
(e.g. db does not exist already) or you don't want to make new dump without
extended inserts (because import is slower). This scipt can solve the problem.

Inspired by: http://blog.lavoie.sl/2014/06/split-mysqldump-extended-inserts.html

Current version is functional enough to do the job in most cases, but is not
optimized, so can use a lot of memory and take a lot of time to finish the job.

Possible enhancements:

- in process_file():
-- readline (one line at a time) instead of readlines, to lower memory usage
-- write (append) processed line into file immediately and free the memory
-- force output file to be different than input file

- in ask_confirmation():
-- use list of allowed answers (e.g. "y", "yes", etc.), not only one option

- in general:
-- use translated strings (localization, e.g. using gettext)

Version: 1.0.0 (2021-05-31)
Author: Marcin Lewicz
License: MIT
"""

import os.path

def main():
        """
        Ask user for file names and process the file.
        """

        file_name = ask_input_file_name("Input file name: ")
        output_file_name = ask_output_file_name("Output file name: ")
        process_file(file_name, output_file_name)


class State:
        """
        Used to store information about quotes and brackets from previous lines.
        """

        # quote started in previous line(s)?
        in_quotes = False
        # number of brackets opened in previous line(s)
        brackets = 0


def process_file(file_name, output_file_name):
        """
        Reads file, adds '\n' before opening brackets and writes changed file.
        """
        
        lines = []
        output_lines = []
        temp_state = State()
        temp_state.in_quotes = False
        temp_state.brackets = 0

        with open(file_name) as f:
                lines = f.readlines()

        print("Processing file: " + file_name + "...")

        lines_count = str(len(lines))
        line_number = 0

        for line in lines:

                line_number += 1

                # inform user that it's still alive
                if line_number % 10000 == 0:
                        print("Processing line " + str(line_number) + "/" + lines_count)
                        
                # do not change empty lines (containing only '\n')
                if len(line) == 1:
                        output_lines.append(line)
                        continue

                # do not change commented lines
                if line[:2] == "--":
                        output_lines.append(line)
                        continue

                processed_line, temp_state = process_line(line, temp_state)

                for p in processed_line:
                        output_lines.append(p)

        print("Done! Input lines: " + str(len(lines)) + ", output lines: " + str(len(output_lines)))

        print("Saving file...")
        with open(output_file_name , "w") as o:
                for l in output_lines:
                        o.write(l)

        print("Done. Output file " + output_file_name + " ready.")


def process_line(line, previous_state):
        """
        Read line, split it before opening brackets if not in quotes nor escaped
        and add '\n' in the end of new lines.
        """

        # opening bracket and/or quote can start in other line
        brackets = previous_state.brackets
        in_quotes = previous_state.in_quotes
        escaped = False
        processed_line = []
        start = 0

        for i in range(len(line)):

                if line[i] == '\\':
                        escaped = not escaped
                        
                elif line[i] == '\'':
                        if escaped:
                                escaped = False
                        else:
                                in_quotes = not in_quotes

                elif line[i] == '(':
                        if not in_quotes:
                                if brackets == 0:
                                        # don't append additional empty line
                                        if i > 0:
                                                processed_line.append(line[start:i] + "\n")
                                        start = i
                                brackets += 1
                        if escaped:
                                escaped = False
                                
                elif line[i] == ')':
                        if not in_quotes:
                                if brackets > 0:
                                        brackets -= 1
                                else:
                                        print("Warning: closing ')' without opening '('!")
                                        print(line)
                        if escaped:
                                escaped = False

                # line[i] other than mentioned above
                elif escaped:
                        escaped = False

        # append remaining part
        processed_line.append(line[start:])

        current_state = State()
        current_state.in_quotes = in_quotes
        current_state.brackets = brackets

        return processed_line, current_state

def ask_output_file_name(message):
        """ Ask user for name of output file. """
        
        file_name = ask_value(message)

        if verify_file_name(file_name):
                return file_name
        else:
                return ask_output_file_name(message)

def ask_input_file_name(message):
        """ Ask user for name of file to be processed. """

        file_name = ask_value(message)

        if file_exists(file_name):
                return file_name
        else:
                print("File not found.")
                return ask_input_file_name(message)

def verify_file_name(file_name):
        """ If file exists, confirm overwriting. """
        
        if file_exists(file_name):
                if ask_confirmation("File exists! Do you want to overwrite file " + file_name + "? "):
                        return True
                else:
                        return False
                              
        # TODO: check if is correct and ready to write
        return True
        

def file_exists(file_name):
        """ Return True if file exists or False if not. """

        if os.path.isfile(file_name):
                return True
        else:
                return False


def ask_value(message):
        """
        Ask user to type some value. Ask again if no answer.

        Arguments:
        - message (string): message to display

        Return (string): value typed by user
        """
        
        answer = input(message)

        if answer == '':
                return ask_value(message)

        return answer

def ask_confirmation(message, yes = 'y', no = 'n', default = False):
        """
        Ask user to confirm something. Ask again if answer other than expected.

        Arguments:
        - message (string): message to print (e.g. "Are you sure?")
        - yes (string): expected value if user confirms
        - no (string): expceted value if user denies
        - default (bool): value to return if user hits Enter

        Return (bool):
        - True if user types string same as argument yes
        - False if user types string same as argument no
        - default value if user doesn't type anything and hit Enter

        Example:
        ask_confirmation("Are you sure?", "yes", "no", True)
        displays:
        Are you sure? [YES/no]:

        Result:
        - if user types no, No, nO, or NO: returns False
        - if user types yes, Yes, YES, or etc.: returns True
        - if user hits Enter (confirms default): returns True
        - if user types anything else, ask again
        """

        if default:
                yes = yes.upper()
                no = no.lower()
        else:
                yes = yes.lower()
                no = no.upper()
                
        long_message = message + " [" + yes + "/" + no + "]: "
        answer = input(long_message).lower()

        if answer == yes.lower():
                return True
        elif answer == no.lower():
                return False
        elif answer == '':
                return default
        else:
                return ask_confirmation(message, yes, no, default)

if __name__ == "__main__":
        main()
