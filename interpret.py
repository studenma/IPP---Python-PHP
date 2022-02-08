#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Projekt: interpret
# Autor: Martin Studeny (xstude23)
# Datum: 5.4.2018

import sys
import argparse
import re
import xml.etree.ElementTree as etree

# TODO zkontrolovat vsechny navratove hodnoty

# funkce, ktera zkontroluje spravnost argumentu
# povolene argumenty jsou --help a --source
# vraci argumenty
# TODO - kontrola jestli funguje spravne
def check_arguments():
	arg = argparse.ArgumentParser(add_help = False)
	arg.add_argument('--help', action = "count", dest="help")
	arg.add_argument('--source', action = "append", default=None, dest="source")
	try:
		arguments = arg.parse_args()
	except:
		print("Argumenty byly zadany spatne", file = sys.stderr)
		sys.exit(10)

	if arguments.help is not None:
		if len(sys.argv) > 2:
			print("Argument --help nesmi byt pouzit s dalsimi prepinaci", file = sys.stderr)
			sys.exit(10);
		else:
			print("Vypisuji napovedu:")
			sys.exit(0)
	if arguments.source is None:
		print("Musi byt zadan argument --source se vstupnim XML souborem", file = sys.stderr)
		sys.exit(10)
	return arguments

# funkce, ktera zkontroluje hlavicku XML, jestli je korenovym elementem program
# + zkontroluje atributy korenoveho elementu
def analyza():
	# TODO - zkontrolovat hlavicku XML
	# kontrola korenoveho elementu
	root = tree.getroot()
	if root.tag == 'program':
		for key in root.attrib:
			if key != 'language':
				if key == 'name' or key == 'description':
					continue
				else:
					print("Chyba: Element program nema spravne atributy", file=sys.stderr)
					sys.exit(31)
		if root.attrib['language'] == 'IPPcode18':
			instrukce(root)
		else:
			print("Chyba: Atribut langauage neni 'IPPcode18'", file=sys.stderr)
			sys.exit(32)
	else:
		print("Chyba: Korenovy element neni program", file=sys.stderr)
		sys.exit(31)

# projdeme vsechny elementy pod korenovym adresarem
# zkontroluje tim jednotlive instrukce
def instrukce(root):
	for instruction in root:
		# pokud najdeme element, ktery se nejmenuje instruction -> chyba
		if instruction.tag != 'instruction':
			print("Chyba: Element se nejmenuje 'instrution'", file=sys.stderr)
			sys.exit(31) # TODO - nejsem si jistej ani u jedne z chyb v tehle funkcii - 31 / 32
		# atributy u elementu instruction musi byt prave 2
		if len(instruction.attrib) != 2:
			print("Chyba: Element instruction musi mit prave 2 atributy", file=sys.stderr)
			sys.exit(31)
		# zkontrolujeme jestli jsou tam spravne atributy 
		for key in instruction.attrib:
			try:
				poradi = instruction.attrib['order']
			except:
				print("Chyba: Element instruction neobsahuje atribut order", file=sys.stderr)
				sys.exit(31)
			try:
				kod = instruction.attrib['opcode']
			except:
				print("Chyba: Element instruction neobsahuje atribut opcode", file=sys.stderr)
				sys.exit(31)

	# v prvnim pruchodu kontrolujeme syntaktickou a lexikalni analyzu
	for i in range(1, len(root)+1):
		tmp = 0
		for instruction in root:
			tmp = tmp + 1
			if int(instruction.attrib['order']) == i:
				# TODO - tady musi byt funkc,e ktera kontroluje vnitrek z hlediska lexikalni a syntakticke analyzy
				vnitrek_instrukce_analyza(instruction)
				break
			if tmp == len(root):
				print("Chyba: Poradi order nedava smysl", file=sys.stderr)
				sys.exit(32)

	# iterace, kterou projdeme vsechny instrukce (od 1 do konce)
	# osetrime tim to, ze nejdriv hledame instrukci cislo jedna a na poradi tedy nezalezi
	# jiz vime, ze poradi dava smysl, takze to nemusime kontrolovat
	a = 0
	for i in range(1, len(root)+1):
		if a == 1:
			break
		for instruction in root:
			if int(instruction.attrib['order']) == i:
				# pokud ma automae nekam skocit, musime vyskocit z tohoto loopu a ve funkci pro jump loop udelat znova od instrukce, kde se ma skocit
				a = automat(instruction, root)
				if a == 1:
					break
				else:
					continue

def check_escape(string):
	if string == "\\010":
		return ""
	sq = re.findall(r'\\\d{3}', string)
	for seq in sq:
		string = string.replace(seq, chr(int(seq[1:])))
	return string

def instrukce_nic(instrukce):
	# zadny child nesmi existovat
	# pokud se dostane za for, musi koncit s chybou
	for child in instrukce:
		print("Chyba: instrukce_nic - nesmi obsahovat zadneho potomka", file=sys.stderr)
		sys.exit(31)

def instrukce_var(instrukce):
	if len(instrukce) != 1:
		print("Chyba: Ve funkci instrukce_var - neodpovida pocet argumentu", file=sys.stderr)
		sys.exit(31)
	if instrukce[0].tag != "arg1":
		print("Chyba: Ve funkci instrukce_var - tag musi byt <arg1>", file=sys.stderr)
		sys.exit(31)

	for child in instrukce:
		if len(child.attrib) != 1:
			print("Chyba: instrukce_var - pocet atributu", file=sys.stderr)
			sys.exit(32) # TODO		
		for key in child.attrib:
			if key != 'type':
				print("Chyba: instrukce_var - neobsahuje atribut 'type'", file=sys.stderr)
				sys.exit(32)
		# TODO - muze byt var psano velkym?
		if child.attrib['type'] != 'var':
			print("Chyba: Nejedna se o promennou", file=sys.stderr)
			sys.exit(32)
		if child.text is None:
			print("Chyba: Spatny format promenne", file=sys.stderr)
			sys.exit(52) # TODO	
		if(re.match('(G|T|L)F@([a-zA-Z]|_|-|\$|&|%|\*)((\w|_|-|\$|&|%|\*)+)?', child.text)):
			continue
		else:
			print("Chyba: Spatny format promenne", file=sys.stderr)
			sys.exit(52) # TODO	

def instrukce_label(instrukce):
	if len(instrukce) != 1:
		print("Chyba: Ve funkci instrukce_label - neodpovida pocet argumentu", file=sys.stderr)
		sys.exit(32)
	if instrukce[0].tag != "arg1":
		print("Chyba: Ve funkci instrukce_label - tag musi byt <arg1>", file=sys.stderr)
		sys.exit(32)
	for child in instrukce:
		if len(child.attrib) != 1:
			print("Chyba: instrukce_label - pocet atributu", file=sys.stderr)
			sys.exit(32) # TODO
		for key in child.attrib:
			if key != 'type':
				print("Chyba: instrukce_label - neobsahuje atribut 'type'", file=sys.stderr)
				sys.exit(32)	
		# TODO - muze byt typ=navesti i velkmi pismeny?
		if child.attrib['type'] != 'label':
			print("Chyba: Nejedna se o navesti", file=sys.stderr)
			sys.exit(32)
		if child.text is None:
			print("Chyba: Spatny format navesti", file=sys.stderr)
			sys.exit(52) # TODO
		if(re.match('([a-zA-Z]|_|-|\$|&|%|\*)((\w|_|-|\$|&|%|\*)+)?', child.text)):
			continue
		else:
			print("Chyba: Spatny format navesti", file=sys.stderr)
			sys.exit(52) # TODO
def findd(s, ch):
    return [i for i, ltr in enumerate(s) if ltr == ch]
def instrukce_symb(instrukce):
	if len(instrukce) != 1:
		print("Chyba: Ve funkci instrukce_symb - neodpovida pocet argumentu", file=sys.stderr)
		sys.exit(32)
	if instrukce[0].tag != "arg1":
		print("Chyba: Ve funkci instrukce_symb - tag musi byt <arg1>", file=sys.stderr)
		sys.exit(32)
	for child in instrukce:
		if len(child.attrib) != 1:
			print("Chyba: instrukce_symb - pocet atributu", file=sys.stderr)
			sys.exit(32) # TODO	
		for key in child.attrib:
			if key != 'type':
				print("Chyba: instrukce_symb - neobsahuje atribut 'type'", file=sys.stderr)
				sys.exit(32)
		if child.attrib['type'] == 'string':
			if child.text is None:
				continue
			else:
				if ' ' in child.text or '\t' in child.text or '\n' in child.text or '#' in child.text:
					print("Chyba: Spatny format stringu", file=sys.stderr)
					sys.exit(32)
				a = findd(child.text, '\\')
				for i in a:
					if child.text[i+1].isdigit():
						if child.text[i+2].isdigit():
							if child.text[i+3].isdigit():
								continue
							else:
								print("Chyba: Spatny format stringu", file=sys.stderr)
								sys.exit(52)
						else:
							print("Chyba: Spatny format stringu", file=sys.stderr)
							sys.exit(52)
					else:
						print("Chyba: Spatny format stringu", file=sys.stderr)
						sys.exit(52)
		elif child.attrib['type'] == 'int':
			if child.text is None:
				print("Chyba: Spatny format integeru", file=sys.stderr)
				sys.exit(52)
			if child.text[0] == '+' or child.text[0] == '-' or child.text[0].isdigit():
				k = 1
			else:
				print("Chyba: Spatny format integeru", file=sys.stderr)
				sys.exit(52)
			if len(child.text) > 1: # TODO - tohle neni otestovane - vzkouset pokud bude interger jen jedna digit
				if child.text[1:].isdigit():
					continue
				else:
					print("Chyba: Spatny format integeru", file=sys.stderr)
					sys.exit(52)
		elif child.attrib['type'] == 'bool':
			if child.text is None:
				print("Chyba: Spatny format boolu", file=sys.stderr)
				sys.exit(52)
			if child.text == 'true' or child.text == 'false':
				continue
			else:
				print("Chyba: Spatny format boolu", file=sys.stderr)
				sys.exit(52)
		elif child.attrib['type'] == 'var':
			if child.text is None:
				print("Chyba: Spatny format boolu", file=sys.stderr)
				sys.exit(52)
			if(re.match('(G|T|L)F@([a-zA-Z]|_|-|\$|&|%|\*)((\w|_|-|\$|&|%|\*)+)?', child.text)):
				continue
			else:
				print("Chyba: Spatny format promenne", file=sys.stderr)
				sys.exit(52) # TODO
		else:
			print("Chyba: Nejedna se o symbol", file=sys.stderr)
			sys.exit(32)	
def instrukce_var_symb(instrukce):
	if len(instrukce) != 2:
		print("Chyba: Ve funkci instrukce_var_symb - neodpovida pocet argumentu", file=sys.stderr)
		sys.exit(32)
	if instrukce[0].tag != "arg1" and instrukce[1].tag != "arg1":
		print("Chyba: Ve funkci instrukce_var_symb - chybi tag arg1", file=sys.stderr)
		sys.exit(32)
	if instrukce[0].tag != "arg2" and instrukce[1].tag != "arg2":
		print("Chyba: Ve funkci instrukce_var_symb - chybi tag arg2", file=sys.stderr)
		sys.exit(32)	
	# tady uz mame dva potomky
	for child in instrukce:
		if len(child.attrib) != 1:
			print("Chyba: instrukce_var_symb - pocet atributu", file=sys.stderr)
			sys.exit(32) # TODO	
		for key in child.attrib:
			if key != 'type':
				print("Chyba: instrukce_var_symb - neobsahuje atribut 'type'", file=sys.stderr)
				sys.exit(32)
		if child.tag == 'arg1':
			if child.attrib['type'] != 'var':
				print("Chyba: instrukce_var_symb - argument 1 neni promenna", file=sys.stderr)
				sys.exit(32)
			if child.text is None:
				print("Chyba: Spatny format promenne", file=sys.stderr)
				sys.exit(52) # TODO	
			if(re.match('(G|T|L)F@([a-zA-Z]|_|-|\$|&|%|\*)((\w|_|-|\$|&|%|\*)+)?', child.text)):
				continue
			else:
				print("Chyba: Spatny format promenne", file=sys.stderr)
				sys.exit(52) # TODO	
		elif child.tag == 'arg2':
			if child.attrib['type'] == 'string':
				if child.text is None:
					continue
				else:
					if ' ' in child.text or '\t' in child.text or '\n' in child.text or '#' in child.text:
						print("Chyba: Spatny format stringu", file=sys.stderr)
						sys.exit(52)
					a = findd(child.text, '\\')
					for i in a:
						if child.text[i+1].isdigit():
							if child.text[i+2].isdigit():
								if child.text[i+3].isdigit():
									continue
								else:
									print("Chyba: Spatny format stringu", file=sys.stderr)
									sys.exit(52)
							else:
								print("Chyba: Spatny format stringu", file=sys.stderr)
								sys.exit(52)
						else:
							print("Chyba: Spatny format stringu", file=sys.stderr)
							sys.exit(52)
			elif child.attrib['type'] == 'int':
				if child.text is None:
					print("Chyba: Spatny format integeru", file=sys.stderr)
					sys.exit(52)
				if child.text[0] == '+' or child.text[0] == '-' or child.text[0].isdigit():
					k = 1
				else:
					print("Chyba: Spatny format integeru", file=sys.stderr)
					sys.exit(52)
				if len(child.text) > 1:
					if child.text[1:].isdigit():
						continue
					else:
						print("Chyba: Spatny format integeru", file=sys.stderr)
						sys.exit(52)
			elif child.attrib['type'] == 'bool':
				if child.text is None:
					print("Chyba: Spatny format boolu", file=sys.stderr)
					sys.exit(52)
				if child.text == 'true' or child.text == 'false':
					continue
				else:
					print("Chyba: Spatny format boolu", file=sys.stderr)
					sys.exit(52)
			elif child.attrib['type'] == 'var':
				if child.text is None:
					print("Chyba: Spatny format promenne", file=sys.stderr)
					sys.exit(52)
				if(re.match('(G|T|L)F@([a-zA-Z]|_|-|\$|&|%|\*)((\w|_|-|\$|&|%|\*)+)?', child.text)):
					continue
				else:
					print("Chyba: Spatny format promenne", file=sys.stderr)
					sys.exit(52) # TODO
			else:
				print("Chyba: Nejedna se o symbol", file=sys.stderr)
				sys.exit(32)	
		else:
			print("Chyba: instrukce_var_symb - fail, kterej by nemel vubec nastat", file=sys.stderr)
			sys.exit(32)
def instrukce_var_symb_symb(instrukce):
	if len(instrukce) != 3:
		print("Chyba: Ve funkci instrukce_var_symb_symb - neodpovida pocet argumentu", file=sys.stderr)
		sys.exit(53)	
	if instrukce[0].tag != "arg1" and instrukce[1].tag != "arg1" and instrukce[2].tag != "arg1":
		print("Chyba: Ve funkci instrukce_var_symb_symb - chybi tag arg1", file=sys.stderr)
		sys.exit(32)	
	if instrukce[0].tag != "arg2" and instrukce[1].tag != "arg2" and instrukce[2].tag != "arg2":
		print("Chyba: Ve funkci instrukce_var_symb_symb - chybi tag arg2", file=sys.stderr)
		sys.exit(32)
	if instrukce[0].tag != "arg3" and instrukce[1].tag != "arg3" and instrukce[2].tag != "arg3":
		print("Chyba: Ve funkci instrukce_var_symb_symb - chybi tag arg3", file=sys.stderr)
		sys.exit(32)
	# tady budeme mit tri potomky
	for child in instrukce:
		if len(child.attrib) != 1:
			print("Chyba: instrukce_var_symb_symb - pocet atributu", file=sys.stderr)
			sys.exit(32) # TODO
		for key in child.attrib:
			if key != 'type':
				print("Chyba: instrukce_var_symb_symb - neobsahuje atribut 'type'", file=sys.stderr)
				sys.exit(32)
		if child.tag == 'arg1':
			if child.attrib['type'] != 'var':
				print("Chyba: instrukce_var_symb_symb - argument 1 neni promenna", file=sys.stderr)
				sys.exit(32)
			if child.text is None:
				print("Chyba: Spatny format promenne", file=sys.stderr)
				sys.exit(52) # TODO	
			if(re.match('(G|T|L)F@([a-zA-Z]|_|-|\$|&|%|\*)((\w|_|-|\$|&|%|\*)+)?', child.text)):
				continue
			else:
				print("Chyba: Spatny format promenne", file=sys.stderr)
				sys.exit(52) # TODO
		elif child.tag == 'arg2':
			if child.attrib['type'] == 'string':
				if child.text is None:
					continue
				else:
					if ' ' in child.text or '\t' in child.text or '\n' in child.text or '#' in child.text:
						print("Chyba: Spatny format stringu", file=sys.stderr)
						sys.exit(52)
					a = findd(child.text, '\\')
					for i in a:
						if child.text[i+1].isdigit():
							if child.text[i+2].isdigit():
								if child.text[i+3].isdigit():
									continue
								else:
									print("Chyba: Spatny format stringu", file=sys.stderr)
									sys.exit(52)
							else:
								print("Chyba: Spatny format stringu", file=sys.stderr)
								sys.exit(52)
						else:
							print("Chyba: Spatny format stringu", file=sys.stderr)
							sys.exit(52)
			elif child.attrib['type'] == 'int':
				if child.text is None:
					print("Chyba: Spatny format integeru", file=sys.stderr)
					sys.exit(52)
				if child.text[0] == '+' or child.text[0] == '-' or child.text[0].isdigit():
					k = 1
				else:
					print("Chyba: Spatny format integeru", file=sys.stderr)
					sys.exit(52)
				if len(child.text) > 1:
					if child.text[1:].isdigit():
						continue
					else:
						print("Chyba: Spatny format integeru", file=sys.stderr)
						sys.exit(52)
			elif child.attrib['type'] == 'bool':
				if child.text is None:
					print("Chyba: Spatny format boolu", file=sys.stderr)
					sys.exit(52)
				if child.text == 'true' or child.text == 'false':
					continue
				else:
					print("Chyba: Spatny format boolu", file=sys.stderr)
					sys.exit(52)
			elif child.attrib['type'] == 'var':
				if child.text is None:
					print("Chyba: Spatny format promenne", file=sys.stderr)
					sys.exit(52)
				if(re.match('(G|T|L)F@([a-zA-Z]|_|-|\$|&|%|\*)((\w|_|-|\$|&|%|\*)+)?', child.text)):
					continue
				else:
					print("Chyba: Spatny format promenne", file=sys.stderr)
					sys.exit(52) # TODO
			else:
				print("Chyba: Nejedna se o symbol", file=sys.stderr)
				sys.exit(32)
		elif child.tag == 'arg3':
			if child.attrib['type'] == 'string':
				if child.text is None:
					continue
				else:
					if ' ' in child.text or '\t' in child.text or '\n' in child.text or '#' in child.text:
						print("Chyba: Spatny format stringu", file=sys.stderr)
						sys.exit(52)
					a = findd(child.text, '\\')
					for i in a:
						if child.text[i+1].isdigit():
							if child.text[i+2].isdigit():
								if child.text[i+3].isdigit():
									continue
								else:
									print("Chyba: Spatny format stringu", file=sys.stderr)
									sys.exit(52)
							else:
								print("Chyba: Spatny format stringu", file=sys.stderr)
								sys.exit(52)
						else:
							print("Chyba: Spatny format stringu", file=sys.stderr)
							sys.exit(52)
			elif child.attrib['type'] == 'int':
				if child.text is None:
					print("Chyba: Spatny format integeru", file=sys.stderr)
					sys.exit(52)
				if child.text[0] == '+' or child.text[0] == '-' or child.text[0].isdigit():
					k = 1
				else:
					print("Chyba: Spatny format integeru", file=sys.stderr)
					sys.exit(52)
				if len(child.text) > 1:
					if child.text[1:].isdigit():
						continue
					else:
						print("Chyba: Spatny format integeru", file=sys.stderr)
						sys.exit(52)
			elif child.attrib['type'] == 'bool':
				if child.text is None:
					print("Chyba: Spatny format boolu", file=sys.stderr)
					sys.exit(52)
				if child.text == 'true' or child.text == 'false':
					continue
				else:
					print("Chyba: Spatny format boolu", file=sys.stderr)
					sys.exit(52)
			elif child.attrib['type'] == 'var':
				if child.text is None:
					print("Chyba: Spatny format promenne", file=sys.stderr)
					sys.exit(52)
				if(re.match('(G|T|L)F@([a-zA-Z]|_|-|\$|&|%|\*)((\w|_|-|\$|&|%|\*)+)?', child.text)):
					continue
				else:
					print("Chyba: Spatny format promenne", file=sys.stderr)
					sys.exit(52) # TODO
			else:
				print("Chyba: Nejedna se o symbol", file=sys.stderr)
				sys.exit(32)	
		else:
			print("Chyba: instrukce_var_symb - fail, kterej by nemel vubec nastat", file=sys.stderr)
			sys.exit(32)
def instrukce_var_type(instrukce):
	if len(instrukce) != 2:
		print("Chyba: Ve funkci instrukce_var_type - neodpovida pocet argumentu", file=sys.stderr)
		sys.exit(32)
	if instrukce[0].tag != "arg1" and instrukce[1].tag != "arg1":
		print("Chyba: Ve funkci instrukce_var_type - chybi tag arg1", file=sys.stderr)
		sys.exit(32)
	if instrukce[0].tag != "arg2" and instrukce[1].tag != "arg2":
		print("Chyba: Ve funkci instrukce_var_type - chybi tag arg2", file=sys.stderr)
		sys.exit(32)	
	# tady uz mame dva potomky
	for child in instrukce:
		if len(child.attrib) != 1:
			print("Chyba: instrukce_var_type - pocet atributu", file=sys.stderr)
			sys.exit(32) # TODO		
		for key in child.attrib:
			if key != 'type':
				print("Chyba: instrukce_var_type - neobsahuje atribut 'type'", file=sys.stderr)
				sys.exit(32)
		if child.tag == 'arg1':
			if child.attrib['type'] != 'var':
				print("Chyba: instrukce_var_type - argument 1 neni promenna", file=sys.stderr)
				sys.exit(32)
			if child.text is None:
				print("Chyba: Spatny format promenne", file=sys.stderr)
				sys.exit(52) # TODO	
			if(re.match('(G|T|L)F@([a-zA-Z]|_|-|\$|&|%|\*)((\w|_|-|\$|&|%|\*)+)?', child.text)):
				continue
			else:
				print("Chyba: Spatny format promenne", file=sys.stderr)
				sys.exit(52) # TODO	
		elif child.tag == 'arg2':
			if child.attrib['type'] != 'type':
				print("Chyba: instrukce_var_type - argument 2 neni type", file=sys.stderr)
				sys.exit(32)
			if child.text is None:
				print("Chyba: Spatny format", file=sys.stderr)
				sys.exit(52) # TODO
			elif child.text == 'int':
				continue
			elif child.text == 'bool':
				continue
			elif child.text == 'string':
				continue
			else:
				print("Chyba: Spatny format type", file=sys.stderr)
				sys.exit(52) # TODO	
		else:
			print("Chyba: instrukce_var_type", file=sys.stderr)
			sys.exit(32)
def instrukce_label_symb_symb(instrukce):
	if len(instrukce) != 3:
		print("Chyba: Ve funkci instrukce_label_symb_symb - neodpovida pocet argumentu", file=sys.stderr)
		sys.exit(32)	
	if instrukce[0].tag != "arg1" and instrukce[1].tag != "arg1" and instrukce[2].tag != "arg1":
		print("Chyba: Ve funkci instrukce_label_symb_symb - chybi tag arg1", file=sys.stderr)
		sys.exit(32)	
	if instrukce[0].tag != "arg2" and instrukce[1].tag != "arg2" and instrukce[2].tag != "arg2":
		print("Chyba: Ve funkci instrukce_label_symb_symb - chybi tag arg2", file=sys.stderr)
		sys.exit(32)
	if instrukce[0].tag != "arg3" and instrukce[1].tag != "arg3" and instrukce[2].tag != "arg3":
		print("Chyba: Ve funkci instrukce_label_symb_symb - chybi tag arg3", file=sys.stderr)
		sys.exit(32)
	# tady budeme mit tri potomky
	for child in instrukce:
		if len(child.attrib) != 1:
			print("Chyba: instrukce_label_symb_symb - pocet atributu", file=sys.stderr)
			sys.exit(32) # TODO
		for key in child.attrib:
			if key != 'type':
				print("Chyba: instrukce_label_symb_symb - neobsahuje atribut 'type'", file=sys.stderr)
				sys.exit(32)
		if child.tag == 'arg1':
			if child.attrib['type'] != 'label':
				print("Chyba: instrukce_label_symb_symb - argument 1 neni label", file=sys.stderr)
				sys.exit(32)
			if child.text is None:
				print("Chyba: Spatny format label", file=sys.stderr)
				sys.exit(52) # TODO	
			if(re.match('([a-zA-Z]|_|-|\$|&|%|\*)((\w|_|-|\$|&|%|\*)+)?', child.text)):
				continue
			else:
				print("Chyba: Spatny format promenne", file=sys.stderr)
				sys.exit(52) # TODO
		elif child.tag == 'arg2':
			if child.attrib['type'] == 'string':
				if child.text is None:
					continue
				else:
					if ' ' in child.text or '\t' in child.text or '\n' in child.text or '#' in child.text:
						print("Chyba: Spatny format stringu", file=sys.stderr)
						sys.exit(52)
					a = findd(child.text, '\\')
					for i in a:
						if child.text[i+1].isdigit():
							if child.text[i+2].isdigit():
								if child.text[i+3].isdigit():
									continue
								else:
									print("Chyba: Spatny format stringu", file=sys.stderr)
									sys.exit(52)
							else:
								print("Chyba: Spatny format stringu", file=sys.stderr)
								sys.exit(52)
						else:
							print("Chyba: Spatny format stringu", file=sys.stderr)
							sys.exit(52)
			elif child.attrib['type'] == 'int':
				if child.text is None:
					print("Chyba: Spatny format integeru", file=sys.stderr)
					sys.exit(52)
				if child.text[0] == '+' or child.text[0] == '-' or child.text[0].isdigit():
					k = 1
				else:
					print("Chyba: Spatny format integeru", file=sys.stderr)
					sys.exit(52)
				if len(child.text) > 1:
					if child.text[1:].isdigit():
						continue
					else:
						print("Chyba: Spatny format integeru", file=sys.stderr)
						sys.exit(52)
			elif child.attrib['type'] == 'bool':
				if child.text is None:
					print("Chyba: Spatny format boolu", file=sys.stderr)
					sys.exit(52)
				if child.text == 'true' or child.text == 'false':
					continue
				else:
					print("Chyba: Spatny format boolu", file=sys.stderr)
					sys.exit(52)
			elif child.attrib['type'] == 'var':
				if child.text is None:
					print("Chyba: Spatny format promenne", file=sys.stderr)
					sys.exit(52)
				if(re.match('(G|T|L)F@([a-zA-Z]|_|-|\$|&|%|\*)((\w|_|-|\$|&|%|\*)+)?', child.text)):
					continue
				else:
					print("Chyba: Spatny format promenne", file=sys.stderr)
					sys.exit(52) # TODO
			else:
				print("Chyba: Nejedna se o symbol", file=sys.stderr)
				sys.exit(32)
		elif child.tag == 'arg3':
			if child.attrib['type'] == 'string':
				if child.text is None:
					continue
				else:
					if ' ' in child.text or '\t' in child.text or '\n' in child.text or '#' in child.text:
						print("Chyba: Spatny format stringu", file=sys.stderr)
						sys.exit(52)
					a = findd(child.text, '\\')
					for i in a:
						if child.text[i+1].isdigit():
							if child.text[i+2].isdigit():
								if child.text[i+3].isdigit():
									continue
								else:
									print("Chyba: Spatny format stringu", file=sys.stderr)
									sys.exit(52)
							else:
								print("Chyba: Spatny format stringu", file=sys.stderr)
								sys.exit(52)
						else:
							print("Chyba: Spatny format stringu", file=sys.stderr)
							sys.exit(52)
			elif child.attrib['type'] == 'int':
				if child.text is None:
					print("Chyba: Spatny format integeru", file=sys.stderr)
					sys.exit(52)
				if child.text[0] == '+' or child.text[0] == '-' or child.text[0].isdigit():
					k = 1
				else:
					print("Chyba: Spatny format integeru", file=sys.stderr)
					sys.exit(52)
				if len(child.text) > 1:
					if child.text[1:].isdigit():
						continue
					else:
						print("Chyba: Spatny format integeru", file=sys.stderr)
						sys.exit(52)
			elif child.attrib['type'] == 'bool':
				if child.text is None:
					print("Chyba: Spatny format boolu", file=sys.stderr)
					sys.exit(52)
				if child.text == 'true' or child.text == 'false':
					continue
				else:
					print("Chyba: Spatny format boolu", file=sys.stderr)
					sys.exit(52)
			elif child.attrib['type'] == 'var':
				if child.text is None:
					print("Chyba: Spatny format promenne", file=sys.stderr)
					sys.exit(52)
				if(re.match('(G|T|L)F@([a-zA-Z]|_|-|\$|&|%|\*)((\w|_|-|\$|&|%|\*)+)?', child.text)):
					continue
				else:
					print("Chyba: Spatny format promenne", file=sys.stderr)
					sys.exit(52) # TODO
			else:
				print("Chyba: Nejedna se o symbol", file=sys.stderr)
				sys.exit(32)	
		else:
			print("Chyba: instrukce_var_symb - fail, kterej by nemel vubec nastat", file=sys.stderr)
			sys.exit(32)	
# funkce, ktera overuje vnitrek instrukce z hlediska lexikalni a syntakticke analyzy
def vnitrek_instrukce_analyza(instrukce):
	for key in instrukce.attrib:
		if key != "order":
			if key != "opcode":
				print("Chyba: atributy", file=sys.stderr)
				sys.exit(32)
	if instrukce.attrib['opcode'] == 'MOVE':
		instrukce_var_symb(instrukce)
	elif instrukce.attrib['opcode'] == 'CREATEFRAME':	
		instrukce_nic(instrukce)
	elif instrukce.attrib['opcode'] == 'PUSHFRAME':	
		instrukce_nic(instrukce)	
	elif instrukce.attrib['opcode'] == 'POPFRAME':
		instrukce_nic(instrukce)	
	elif instrukce.attrib['opcode'] == 'DEFVAR':
		instrukce_var(instrukce)	
	elif instrukce.attrib['opcode'] == 'CALL':	
		instrukce_label(instrukce)
	elif instrukce.attrib['opcode'] == 'RETURN':
		instrukce_nic(instrukce)		
	elif instrukce.attrib['opcode'] == 'PUSHS':	
		instrukce_symb(instrukce)
	elif instrukce.attrib['opcode'] == 'POPS':	
		instrukce_var(instrukce)
	elif instrukce.attrib['opcode'] == 'ADD':
		instrukce_var_symb_symb(instrukce)	
	elif instrukce.attrib['opcode'] == 'SUB':
		instrukce_var_symb_symb(instrukce)	
	elif instrukce.attrib['opcode'] == 'MUL':
		instrukce_var_symb_symb(instrukce)			
	elif instrukce.attrib['opcode'] == 'IDIV':	
		instrukce_var_symb_symb(instrukce)	
	elif instrukce.attrib['opcode'] == 'LT':
		instrukce_var_symb_symb(instrukce)			
	elif instrukce.attrib['opcode'] == 'GT':
		instrukce_var_symb_symb(instrukce)		
	elif instrukce.attrib['opcode'] == 'EQ':	
		instrukce_var_symb_symb(instrukce)	
	elif instrukce.attrib['opcode'] == 'AND':	
		instrukce_var_symb_symb(instrukce)	
	elif instrukce.attrib['opcode'] == 'OR':
		instrukce_var_symb_symb(instrukce)		
	elif instrukce.attrib['opcode'] == 'NOT':	
		instrukce_var_symb(instrukce)	
	elif instrukce.attrib['opcode'] == 'INT2CHAR':	
		instrukce_var_symb(instrukce)
	elif instrukce.attrib['opcode'] == 'STRI2INT':	
		instrukce_var_symb_symb(instrukce)	
	elif instrukce.attrib['opcode'] == 'READ':	
		instrukce_var_type(instrukce)
	elif instrukce.attrib['opcode'] == 'WRITE':	
		instrukce_symb(instrukce)
	elif instrukce.attrib['opcode'] == 'CONCAT':	
		instrukce_var_symb_symb(instrukce)	
	elif instrukce.attrib['opcode'] == 'STRLEN':
		instrukce_var_symb(instrukce)
	elif instrukce.attrib['opcode'] == 'GETCHAR':	
		instrukce_var_symb_symb(instrukce)	
	elif instrukce.attrib['opcode'] == 'SETCHAR':
		instrukce_var_symb_symb(instrukce)		
	elif instrukce.attrib['opcode'] == 'TYPE':	
		instrukce_var_symb(instrukce)
	elif instrukce.attrib['opcode'] == 'LABEL':	
		instrukce_labell(instrukce)
	elif instrukce.attrib['opcode'] == 'JUMP':
		instrukce_label(instrukce)	
	elif instrukce.attrib['opcode'] == 'JUMPIFEQ':	
		instrukce_label_symb_symb(instrukce)
	elif instrukce.attrib['opcode'] == 'JUMPIFNEQ':	
		instrukce_label_symb_symb(instrukce)
	elif instrukce.attrib['opcode'] == 'DPRINT':
		instrukce_symb(instrukce)	
	elif instrukce.attrib['opcode'] == 'BREAK':
		instrukce_nic(instrukce)
	else:
		print("Chyba: Opcode neexistuje", file=sys.stderr)
		sys.exit(32) # TODO
	# TODO - ze mame vsechny argumenty
	# TODO - argumenty maji spravne cislovani
	# TODO - existujici typ
	# TODO - ocekavany typ
	# TODO - int - prazdno? chyba + bool prazndy, nebo spatnej format
	# celkove kontrola formatu u strongu, bool, int, promenne
# funkce, ktera rozhoduje o jakou instrukci se jedna
def automat(instrukce, root):
	return_value = 0
	if instrukce.attrib['opcode'] == 'MOVE':
		instrukce_move(instrukce)
	elif instrukce.attrib['opcode'] == 'CREATEFRAME':	
		instrukce_createframe(instrukce)
	elif instrukce.attrib['opcode'] == 'PUSHFRAME':	
		instrukce_pushframe(instrukce)	
	elif instrukce.attrib['opcode'] == 'POPFRAME':
		instrukce_popframe(instrukce)	
	elif instrukce.attrib['opcode'] == 'DEFVAR':
		instrukce_defvar(instrukce)	
	elif instrukce.attrib['opcode'] == 'CALL':	
		instrukce_call(instrukce, root)
	elif instrukce.attrib['opcode'] == 'RETURN':
		instrukce_return(instrukce, root)		
	elif instrukce.attrib['opcode'] == 'PUSHS':	
		instrukce_pushs(instrukce)
	elif instrukce.attrib['opcode'] == 'POPS':	
		instrukce_pops(instrukce)
	elif instrukce.attrib['opcode'] == 'ADD':
		instrukce_add(instrukce)	
	elif instrukce.attrib['opcode'] == 'SUB':
		instrukce_sub(instrukce)	
	elif instrukce.attrib['opcode'] == 'MUL':
		instrukce_mul(instrukce)			
	elif instrukce.attrib['opcode'] == 'IDIV':	
		instrukce_idiv(instrukce)	
	elif instrukce.attrib['opcode'] == 'LT':
		instrukce_lt(instrukce)			
	elif instrukce.attrib['opcode'] == 'GT':
		instrukce_gt(instrukce)		
	elif instrukce.attrib['opcode'] == 'EQ':	
		instrukce_eq(instrukce)	
	elif instrukce.attrib['opcode'] == 'AND':	
		instrukce_and(instrukce)	
	elif instrukce.attrib['opcode'] == 'OR':
		instrukce_or(instrukce)		
	elif instrukce.attrib['opcode'] == 'NOT':	
		instrukce_not(instrukce)	
	elif instrukce.attrib['opcode'] == 'INT2CHAR':	
		instrukce_int2char(instrukce)
	elif instrukce.attrib['opcode'] == 'STRI2INT':	
		instrukce_stri2int(instrukce)	
	elif instrukce.attrib['opcode'] == 'READ':	
		instrukce_read(instrukce)
	elif instrukce.attrib['opcode'] == 'WRITE':	
		instrukce_write(instrukce)
	elif instrukce.attrib['opcode'] == 'CONCAT':	
		instrukce_concat(instrukce)	
	elif instrukce.attrib['opcode'] == 'STRLEN':
		instrukce_strlen(instrukce)
	elif instrukce.attrib['opcode'] == 'GETCHAR':	
		instrukce_getchar(instrukce)	
	elif instrukce.attrib['opcode'] == 'SETCHAR':
		instrukce_setchar(instrukce)		
	elif instrukce.attrib['opcode'] == 'TYPE':	
		instrukce_type(instrukce)
	elif instrukce.attrib['opcode'] == 'LABEL':	
		a = 5
		#instrukce_labell(instrukce)
	elif instrukce.attrib['opcode'] == 'JUMP':
		jump = instrukce_jump(instrukce, root)	
		# pokud se ma skocit, musime zrusit predchozi loop
		if jump == 1:
			return_value = 1
	elif instrukce.attrib['opcode'] == 'JUMPIFEQ':	
		jump = instrukce_jumpifeq(instrukce, root)
		if jump == 1:
			return_value = 1
	elif instrukce.attrib['opcode'] == 'JUMPIFNEQ':	
		jump = instrukce_jumpifneq(instrukce, root)
		if jump == 1:
			return_value = 1
	elif instrukce.attrib['opcode'] == 'DPRINT':
		instrukce_drpint(instrukce)	
	elif instrukce.attrib['opcode'] == 'BREAK':
		instrukce_break(instrukce)
	else:
		print("Chyba: Opcode neexistuje", file=sys.stderr)
		sys.exit(32) # TODO
	return return_value

# DO:
# promenna = var
# ramec_promenne = GF / LF / TF
# Z:
# hodnota = 16515 / sdfsf / true / var
# ramec = GF/LF/TF/ None
# typ_hodnoty = string/bool/int/None - nevime
# TODO - poradne otestovat
def pridat_do_promenne(promenna, ramec_promenne, hodnota, ramec, typ_hodnoty):
	# print("----")
	# print(promenna)
	# print(ramec_promenne)
	# print(hodnota)
	# print(ramec)
	# print(typ_hodnoty)
	# print("----")
	# hodnota je ulozena v promenne v ramci GF
	if ramec == "GF":
		# ukladame do GF z GF
		if ramec_promenne == "GF":
			global_frame[promenna] = global_frame[hodnota]
			# pokud jeste nezname, jake hodnoty ma byt promenna pro prirazeni
			if typ_hodnoty is None:
				global_frame_types[promenna] = global_frame_types[hodnota]
			else:
				global_frame_types[promenna] = typ_hodnoty
		# ukladame do LF z GF
		elif ramec_promenne == "LF":	
			local_frame[promenna] = global_frame[hodnota]
			if typ_hodnoty is None:
				local_frame_types[promenna] = global_frame_types[hodnota]
			else:
				local_frame_types[promenna] = typ_hodnoty
		# ukladame do TF z GF
		elif ramec_promenne == "TF":
			if temp_frame_defined == 0:
				print("Chyba: Nemel bych pridavat do TF, kdyz neni inicializovan", file=sys.stderr)
				sys.exit(55) # TODO	
			temp_frame[promenna] = global_frame[hodnota]
			if typ_hodnoty is None:
				temp_frame_types[promenna] = global_frame_types[hodnota]
			else:
				temp_frame_types[promenna] = typ_hodnoty
		else:
			print("Chyba: tady se to nemuze dostat", file=sys.stderr)
			sys.exit(25) # TODO	
	# hodnota je ulozena v promenne v ramci LF
	elif ramec == "LF":
		# ukladame do GF z LF
		if ramec_promenne == "GF":
			global_frame[promenna] = local_frame[hodnota]
			if typ_hodnoty is None:
				global_frame_types[promenna] = local_frame_types[hodnota]
			else:
				global_frame_types[promenna] = typ_hodnoty
		# ukladame do LF z LF
		elif ramec_promenne == "LF":	
			local_frame[promenna] = local_frame[hodnota]
			if typ_hodnoty is None:
				local_frame_types[promenna] = local_frame_types[hodnota]
			else:
				local_frame_types[promenna] = typ_hodnoty
		# ukladame do TF z LF
		elif ramec_promenne == "TF":
			if temp_frame_defined == 0:
				print("Chyba: Nemel bych pridavat do TF, kdyz neni inicializovan", file=sys.stderr)
				sys.exit(55) # TODO	
			temp_frame[promenna] = local_frame[hodnota]
			if typ_hodnoty is None:
				temp_frame_types[promenna] = local_frame_types[hodnota]
			else:
				temp_frame_types[promenna] = typ_hodnoty
		else:
			print("Chyba: tady se to nemuze dostat", file=sys.stderr)
			sys.exit(25) # TODO	
	# hodnota je ulozena v promenne v ramci TF
	elif ramec == "TF":
		if temp_frame_defined == 0:
			print("Chyba: Nemel bych pridavat do TF, kdyz neni inicializovan", file=sys.stderr)
			sys.exit(55) # TODO			
		# ukladame do GF z TF
		if ramec_promenne == "GF":
			global_frame[promenna] = temp_frame[hodnota]
			if typ_hodnoty is None:
				global_frame_types[promenna] = temp_frame_types[hodnota]
			else:
				global_frame_types[promenna] = typ_hodnoty
		# ukladame do LF z TF
		elif ramec_promenne == "LF":	
			local_frame[promenna] = temp_frame[hodnota]
			if typ_hodnoty is None:
				local_frame_types[promenna] = temp_frame_types[hodnota]
			else:
				local_frame_types[promenna] = typ_hodnoty
		# ukladame do TF z TF
		elif ramec_promenne == "TF":
			temp_frame[promenna] = temp_frame[hodnota]
			if typ_hodnoty is None:
				temp_frame_types[promenna] = temp_frame_types[hodnota]
			else:
				temp_frame_types[promenna] = typ_hodnoty
		else:
			print("Chyba: tady se to nemuze dostat", file=sys.stderr)
			sys.exit(25) # TODO	
	# hodnota neni ulozena v promenne - hodnota je primo hodnota, kterou chceme pridat do ormenne
	elif ramec is None:
		if typ_hodnoty is None:
			print("Chyba: typ hodnoty je None: tady by melo byt jasne definovano", file=sys.stderr)
			sys.exit(25) # TODO	
		if ramec_promenne == "GF":
			global_frame[promenna] = hodnota
			global_frame_types[promenna] = typ_hodnoty
		elif ramec_promenne == "LF":	
			local_frame[promenna] = hodnota
			local_frame_types[promenna] = typ_hodnoty
		elif ramec_promenne == "TF":
			temp_frame[promenna] = hodnota
			temp_frame_types[promenna] = typ_hodnoty
		else:
			print("Chyba: tady se to nemuze dostat", file=sys.stderr)
			sys.exit(25) # TODO	
	else:
		print("Chyba: tady se to nemuze dostat", file=sys.stderr)
		sys.exit(25) # TODO

# funkce, ktera zkontroluje, zda promenna jiz byla deklarovana
# ramec 1 - LF, 2 - GF, 3 - TF
# funkce vraci 0, pokud promenna jiz byla deklarovana
# jinak vraci 1
def is_declared(var, ramec):
	if ramec == "LF":
		if local_frame.get(var, 1) == 1:
			return 1
		else:
			return 0
	elif ramec == "GF":
		if global_frame.get(var,1) == 1:
			return 1
		else:
			return 0
	elif ramec == "TF":
		if temp_frame.get(var, 1) == 1:
			return 1
		else:
			return 0
	else:
		print("Chyba: ...Ve funkci is_declared - ramec neexistuje", file=sys.stderr)
		sys.exit(26)
	return 0

# funkce, ktera overi, zda je promenna pozadovaneho typu
# predpoklada se, ze jiz vime, ze je promenna deklarovana
def je_v_promenne_typ(var, ramec, typ):
	if ramec == "GF":
		if global_frame_types[var] == typ:
			return 0
		else:
			return 1
	elif ramec == "LF":
		if local_frame_types[var] == typ:
			return 0
		else:
			return 1
	elif ramec == "TF":
		if temp_frame_types[var] == typ:
			return 0
		else:
			return 1
	else:
		print("Chyba: Neexistujici ramec - nemelo by se dostat az sem", file=sys.stderr)
		sys.exit(26)	
	return 1

def vrat_hodnotu_promenne(var, ramec):
	if ramec == "GF":
		return global_frame[var]
	elif ramec == "LF":
		return local_frame[var]
	elif ramec == "TF":
		return temp_frame[var]
	else:
		print("Chyba: Neexistujici ramec - nemelo by se dostat az sem", file=sys.stderr)
		sys.exit(26) # TODO	
	return 1

def vrat_typ_promenne(var, ramec):
	if ramec == "GF":
		return global_frame_types[var]
	elif ramec == "LF":
		return local_frame_types[var]
	elif ramec == "TF":
		return temp_frame_types[var]
	else:
		print("Chyba: Neexistujici ramec - nemelo by se dostat az sem", file=sys.stderr)
		sys.exit(26) # TODO	
	return 1
# TODO - co kdyz pridavame do TF, kdyz neni inicializovan
def instrukce_move(instrukce):
	var = instrukce.find("arg1")
	symb = instrukce.find("arg2")
	if var.text[:3] == "GF@":
		var_frame = "GF"
	elif var.text[:3] == "LF@":	
		var_frame = "LF"
		if not zasobnik_volani:
			print("Chyba: zasobnik volani", file=sys.stderr)
			sys.exit(55) # TODO
	elif var.text[:3] == "TF@":
		var_frame = "TF"
		if temp_frame_defined == 0:
			print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
			sys.exit(55) # TODO
	else:
		print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
		sys.exit(27) # TODO

	if is_declared(var.text[3:],var_frame) == 0:
		if symb.attrib['type'] == "var":
			if symb.text[:3] == "GF@":
				symb_frame = "GF"
			elif symb.text[:3] == "LF@":
				symb_frame = "LF"
				if not zasobnik_volani:
					print("Chyba: zasobnik volani", file=sys.stderr)
					sys.exit(55) # TODO
			elif symb.text[:3] == "TF@":
				symb_frame = "TF"
				if temp_frame_defined == 0:
					print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
					sys.exit(55) # TODO
			else:
				print("Chyba: 1Tady by se to nikdy dostta nemelo", file=sys.stderr)
				sys.exit(27) # TODO
			if is_declared(symb.text[3:], symb_frame) == 0:
				# DO:
				# promenna = var
				# ramec_promenne = GF / LF / TF
				# Z:
				# hodnota = 16515 / sdfsf / true / var
				# ramec = GF/LF/TF/ None
				# typ_hodnoty = string/bool/int/None - nevime				
				pridat_do_promenne(var.text[3:], var_frame, symb.text[3:], symb_frame, None)
			else:
				print("Chyba: Sem se dto nesmi dostat", file=sys.stderr)
				sys.exit(27) # TODO
		elif symb.attrib['type'] == "string":
			if symb.text is None:
				tmp = ""
			else:
				tmp = symb.text
			# DO:
			# promenna = var
			# ramec_promenne = GF / LF / TF
			# Z:
			# hodnota = 16515 / sdfsf / true / var
			# ramec = GF/LF/TF/ None
			# typ_hodnoty = string/bool/int/None - nevime
			pridat_do_promenne(var.text[3:], var_frame, tmp, None, "string")
		elif symb.attrib['type'] == "int":
			tmp = int(symb.text)
			pridat_do_promenne(var.text[3:], var_frame, tmp, None, "int")
		elif symb.attrib['type'] == "bool":	
			if symb.text.lower() == 'true':
				# DO:
				# promenna = var
				# ramec_promenne = GF / LF / TF
				# Z:
				# hodnota = 16515 / sdfsf / true / var
				# ramec = GF/LF/TF/ None
				# typ_hodnoty = string/bool/int/None - nevime
				pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
			elif symb.text.lower() == 'false':
				pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
			else:
				print("Chyba: Sem se dto nesmi dostat", file=sys.stderr)
				sys.exit(27) # TODO
		else:
			print("Chyba: Sem se dto nesmi dostat", file=sys.stderr)
			sys.exit(27) # TODO
	else:
		print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
		sys.exit(54) # TODO
def instrukce_createframe(instrukce):
	# nejprve vyprazdnime puvodni docasny ramec
	temp_frame.clear()
	temp_frame_types.clear()
	globals()['temp_frame_defined'] = 1
def instrukce_pushframe(instrukce):
	if temp_frame_defined == 0:
		print("Chyba: Pokus o pristup k nedefinovanem TF ramci", file=sys.stderr)
		sys.exit(55) # TODO
	tmp = temp_frame.copy()
	tmp_typ = temp_frame_types.copy()
	zasobnik_lokalnich_ramcu.append(tmp)
	zasobnik_lokalnich_ramcu_typ.append(tmp_typ)
	temp_frame.clear()
	temp_frame_types.clear()
	globals()['temp_frame_defined'] = 0
def instrukce_popframe(instrukce):
	if temp_frame_defined == 0:
		print("Chyba: Pokus o pristup k nedefinovanem TF ramci", file=sys.stderr)
		sys.exit(55) # TODO
	try:
		tmp = zasobnik_lokalnich_ramcu.pop()
		tmp_typ = zasobnik_lokalnich_ramcu_typ.pop()		
	except:
		print("Chyba: Zadny ramec LF neni k dispozici", file=sys.stderr)
		sys.exit(55) # TODO

	globals()['temp_frame'] = tmp.copy()
	globals()['temp_frame_types'] = tmp_typ.copy()
# TODO - LF a TF
def instrukce_defvar(instrukce):
	var = instrukce.find("arg1")
	if var.text[:3] == "GF@":
		var_frame = "GF"
	elif var.text[:3] == "LF@":
		var_frame = "LF"
		if not zasobnik_volani:
			print("Chyba: zasobnik volani", file=sys.stderr)
			sys.exit(55) # TODO
	elif var.text[:3] == "TF@":
		var_frame = "TF"
		if temp_frame_defined == 0:
			print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
			sys.exit(55) # TODO
	else:
		print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
		sys.exit(28) # TODO

	if is_declared(var.text[3:], var_frame) == 1:
		# DO:
		# promenna = var
		# ramec_promenne = GF / LF / TF
		# Z:
		# hodnota = 16515 / sdfsf / true / var
		# ramec = GF/LF/TF/ None
		# typ_hodnoty = string/bool/int/None - nevime
		# TODO - poradne otestovat
		pridat_do_promenne(var.text[3:], var_frame, "", None, "")
	else:
		print("Chyba: Pokousite se deklarovat promennou, ktera jiz byla driv dekalrovana", file=sys.stderr)
		sys.exit(30) # TODO
def instrukce_call(instrukce, root):
	jump = 0
	label = instrukce.find("arg1")
	if label.attrib['type'] == "label":
		if label_exist(label.text) == 0:
			zasobnik_volani.append(instrukce.attrib['order']) # musime si zapamatova,t ze po returnu musime pokracovat dal od tehle instrukce+1
			# v pripade, ze je label na posledni instrukci, tak nefunguje spravne
			# tahle podminak by to mela osetrit
			if int(label_list[label.text]) == len(root)+1:
				#ukoncime program bez chyby
				sys.exit(0)
			for i in range(int(label_list[label.text]), len(root)+1):
				for instruction in root:
					if int(instruction.attrib['order']) == i:
						automat(instruction, root)
						jump = 1 # znaci, se doslo ke skoku a bude se muset ukoncit predchozi loop
		else:
			print("Chyba: Snazite se skocit na neexistujici label", file=sys.stderr)
			sys.exit(52) # TODO
	else:
		print("Chyba: ocekava se label", file=sys.stderr)
		sys.exit(32) # TODO
	if jump == 1:
		return 1
	else:
		return 0
def instrukce_return(instrukce, root):
	try:
		a = zasobnik_volani.pop()
	except:
		print("Chyba: zasobnik volani je prazndy a snazite se popnout hodnotu", file=sys.stderr)
		sys.exit(56)

	# v pripade, ze je call na posledni instrukci, tak nefunguje spravne
	# tahle podminak by to mela osetrit
	# TODO - otestovat, jestli funguje
	if int(a) == len(root):
		#ukoncime program bez chyby
		sys.exit(0)
	for i in range(int(a)+1, len(root)+1):
		for instruction in root:
			if int(instruction.attrib['order']) == i:
				automat(instruction, root) # TODO - u vsech moznych skoku bychom mel kontrolovat to co v zakaldnim cyklu asi
				jump = 1 # znaci, se doslo ke skoku a bude se muset ukoncit predchozi loop
	sys.exit(0)

def instrukce_pushs(instrukce):
	symb = instrukce.find("arg1")

	if symb.attrib['type'] == "var":
		if symb.text[:3] == "GF@":
			symb_frame = "GF"
		elif symb.text[:3] == "LF@":
			symb_frame = "LF"
			if not zasobnik_volani:
				print("Chyba: zasobnik volani", file=sys.stderr)
				sys.exit(55) # TODO
		elif symb.text[:3] == "TF@":
			symb_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
			sys.exit(43) # TODO

	if symb.attrib['type'] == 'var':
		if is_declared(symb.text[3:],symb_frame) == 0:
			if je_v_promenne_typ(symb.text[3:], symb_frame, "string") == 0:
				tmp = vrat_hodnotu_promenne(symb.text[3:], symb_frame)  
				tmp2 = vrat_typ_promenne(symb.text[3:], symb_frame)  
				datovy_zasobnik_typ.append("string")
				datovy_zasobnik.append(tmp)
			elif je_v_promenne_typ(symb.text[3:], symb_frame, "int") == 0:
				tmp = vrat_hodnotu_promenne(symb.text[3:], symb_frame)  
				tmp2 = vrat_typ_promenne(symb.text[3:], symb_frame)  
				tmp = int(tmp)
				datovy_zasobnik_typ.append("int")
				datovy_zasobnik.append(tmp)
			elif je_v_promenne_typ(symb.text[3:], symb_frame, "bool") == 0:
				tmp = vrat_hodnotu_promenne(symb.text[3:], symb_frame)  
				tmp2 = vrat_typ_promenne(symb.text[3:], symb_frame)  
				datovy_zasobnik_typ.append("bool")
				datovy_zasobnik.append(tmp)
			else:
				print("Chyba: 1 tady by se to dostat nemelo", file=sys.stderr)
				sys.exit(53) # TODO
		else:
			print("Chyba: 1 tady by se to dostat nemelo", file=sys.stderr)
			sys.exit(54) # TODO
	elif symb.attrib['type'] == 'string':
		tmp = symb.text  
		datovy_zasobnik_typ.append("string")
		datovy_zasobnik.append(tmp)
	elif symb.attrib['type'] == 'int':
		tmp = symb.text  
		tmp = int(tmp)
		datovy_zasobnik_typ.append("int")
		datovy_zasobnik.append(tmp)
	elif symb.attrib['type'] == 'bool':
		tmp = symb.text  
		datovy_zasobnik_typ.append("bool")
		datovy_zasobnik.append(tmp)
	else:
		print("Chyba: 2 tady by se to dostat nemelo", file=sys.stderr)
		sys.exit(43) # TODO
def instrukce_pops(instrukce):
	var = instrukce.find("arg1")
	if var.text[:3] == "GF@":
		var_frame = "GF"
	elif var.text[:3] == "LF@":
		var_frame = "LF"
		if not zasobnik_volani:
			print("Chyba: zasobnik volani", file=sys.stderr)
			sys.exit(55) # TODO
	elif var.text[:3] == "TF@":
		var_frame = "TF"
		if temp_frame_defined == 0:
			print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
			sys.exit(55) # TODO
	else:
		print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
		sys.exit(28) # TODO

	if is_declared(var.text[3:], var_frame) == 1:
		if not datovy_zasobnik_typ:
			print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
			sys.exit(56) # TODO			
		tmp_typ = datovy_zasobnik_typ.pop()
		tmp = datovy_zasobnik.pop()
		# DO:
		# promenna = var
		# ramec_promenne = GF / LF / TF
		# Z:
		# hodnota = 16515 / sdfsf / true / var
		# ramec = GF/LF/TF/ None
		# typ_hodnoty = string/bool/int/None - nevime
		pridat_do_promenne(var.text[3:], var_frame, "", tmp, tmp_typ)
	else:
		print("Chyba: ", file=sys.stderr)
		sys.exit(55) # TODO
def string_to_cislo(string):
	if string[0].isdigit():
		cislo = int(string[0])
		return cislo
	elif string[0] == '+':
		return int(string)
	elif string[0] == '-':
		return int(string)
	else:
		print("Chyba: ve funkci string_to_cislo", file=sys.stderr)
		sys.exit(41) # TODO

# TODO - symboly musi byt typu int, coz bych mel kontrolovat asi uz v prvnim behu
# TODO - muze byt symbol promenna, ktera obsahuje promennou typu int?
def instrukce_add(instrukce):
	var = instrukce.find("arg1")
	symb2 = instrukce.find("arg2")
	symb3 = instrukce.find("arg3")
	# urceni ramce var
	if var.text[:3] == "GF@":
		var_frame = "GF"
	elif var.text[:3] == "LF@":	
		var_frame = "LF"
		if not zasobnik_volani:
			print("Chyba: zasobnik volani", file=sys.stderr)
			sys.exit(55) # TODO		
	elif var.text[:3] == "TF@":
		var_frame = "TF"
		if temp_frame_defined == 0:
			print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
			sys.exit(55) # TODO
	else:
		print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
		sys.exit(42) # TODO

	if symb2.attrib['type'] == "var":
		if var.text[:3] == "GF@":
			symb2_frame = "GF"
		elif symb2.text[:3] == "LF@":	
			symb2_frame = "LF"
		elif symb2.text[:3] == "TF@":
			symb2_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
			sys.exit(42) # TODO

	if symb3.attrib['type'] == "var":
		if symb3.text[:3] == "GF@":
			symb3_frame = "GF"
		elif symb3.text[:3] == "LF@":	
			symb3_frame = "LF"
		elif symb3.text[:3] == "TF@":
			symb3_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
			sys.exit(42) # TODO

	# promenna, do ktere mame ukladat musi byt deklarovana
	if is_declared(var.text[3:], var_frame) == 0:
		# prvni symbol je promenna
		if symb2.attrib['type'] == 'var':
			if is_declared(symb2.text[3:], symb2_frame) == 0:
				# prvni var->int
				if je_v_promenne_typ(symb2.text[3:], symb2_frame, "int") == 0:
					#prvni var->int, druhy var
					if symb3.attrib['type'] == 'var':
						# prvni var->int, druhy var->int
						if je_v_promenne_typ(symb3.text[3:], symb3_frame, "int") == 0:
							tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame)
							cislo1 = string_to_cislo(tmp)
							tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame)
							cislo2 = string_to_cislo(tmp)
							vysledek = cislo1 + cislo2
							# DO:
							# promenna = var
							# ramec_promenne = GF / LF / TF
							# Z:
							# hodnota = 16515 / sdfsf / true / var
							# ramec = GF/LF/TF/ None
							# typ_hodnoty = string/bool/int/None - nevime
							pridat_do_promenne(var.text[3:], var_frame, vysledek, None, "int")
						# prvni var->int, druhy var->string/bool
						else:
							print("Chyba: instrukce_add - spatny typ", file=sys.stderr)
							sys.exit(53) # TODO
					elif symb3.attrib['type'] == 'int':
						tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame)
						cislo1 = string_to_cislo(tmp)
						cislo2 = string_to_cislo(symb3.text)
						vysledek = cislo1 + cislo2
						pridat_do_promenne(var.text[3:], var_frame, vysledek, None, "int")					
					else:
						print("Chyba: instrukce_add - spatny typ", file=sys.stderr)
						sys.exit(53) # TODO
				# prvni je var, ale neni int
				else:
					print("Chyba: instrukce_add - neni int", file=sys.stderr)
					sys.exit(53) # TODO
				return
			else:
				print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
				sys.exit(54) # TODO				
		# prvni symbol je primo integer
		elif symb2.attrib['type'] == 'int':
			# prvni symbol je int, druhy var
			if symb3.attrib['type'] == 'var':
				if is_declared(symb3.text[3:], symb3_frame) == 0:
					if je_v_promenne_typ(symb3.text[3:], symb3_frame, "int") == 0:
						cislo1 = string_to_cislo(symb2.text)
						tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
						cislo2 = string_to_cislo(tmp)
						vysledek = cislo1 + cislo2
						pridat_do_promenne(var.text[3:], var_frame, vysledek, None, "int")
					else:
						print("Chyba: instrukce_add - neni int", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
					sys.exit(54) # TODO
			# oba symboly jsou primo typu int
			elif symb3.attrib['type'] == 'int':
				cislo1 = string_to_cislo(symb2.text)
				cislo2 = string_to_cislo(symb3.text)
				vysledek = cislo1 + cislo2
				pridat_do_promenne(var.text[3:], var_frame, vysledek, None, "int")
			else:
				print("Chyba: instrukce_add - neni int", file=sys.stderr)
				sys.exit(53) # TODO
		else:
			print("Chyba: instrukce_add - spatny typ - musi byt integer", file=sys.stderr)
			sys.exit(53) # TODO
	else:
		print("Chyba: Snazite se provest operaci ADD nad neexistujici promennou", file=sys.stderr)
		sys.exit(54) # TODO
# TODO - symboly musi byt typu int, coz bych mel kontrolovat asi uz v prvnim behu
# TODO - muze byt symbol promenna, ktera obsahuje promennou typu int?
def instrukce_sub(instrukce):
	var = instrukce.find("arg1")
	symb2 = instrukce.find("arg2")
	symb3 = instrukce.find("arg3")

	if var.text[:3] == "GF@":
		var_frame = "GF"
	elif var.text[:3] == "LF@":	
		var_frame = "LF"
		if not zasobnik_volani:
			print("Chyba: zasobnik volani", file=sys.stderr)
			sys.exit(55) # TODO
	elif var.text[:3] == "TF@":
		var_frame = "TF"
		if temp_frame_defined == 0:
			print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
			sys.exit(55) # TODO
	else:
		print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
		sys.exit(43) # TODO

	if symb2.attrib['type'] == "var":
		if var.text[:3] == "GF@":
			symb2_frame = "GF"
		elif symb2.text[:3] == "LF@":	
			symb2_frame = "LF"
		elif symb2.text[:3] == "TF@":
			symb2_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
			sys.exit(43) # TODO

	if symb3.attrib['type'] == "var":
		if symb3.text[:3] == "GF@":
			symb3_frame = "GF"
		elif symb3.text[:3] == "LF@":	
			symb3_frame = "LF"
		elif symb3.text[:3] == "TF@":
			symb3_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
			sys.exit(43) # TODO

	# promenna, do ktere mame ukladat vysledek musi byt deklarovana
	if is_declared(var.text[3:],var_frame) == 0:
		#prvni symbol je promenna
		if symb2.attrib['type'] == 'var':
			if is_declared(symb2.text[3:], symb2_frame) == 0:
				# prvni symbol je var->int
				if je_v_promenne_typ(symb2.text[3:], symb2_frame, "int") == 0:
					# druhy symbol je var
					if symb3.attrib['type'] == 'var':
						if is_declared(symb3.text[3:], symb3_frame) == 0:
							# pvni symbol je var->int, druhy taky var->int
							if je_v_promenne_typ(symb3.text[3:], symb3_frame, "int") == 0:
								tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame)
								cislo1 = string_to_cislo(tmp)
								tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame)
								cislo2 = string_to_cislo(tmp)
								vysledek = cislo1 - cislo2
								pridat_do_promenne(var.text[3:], var_frame, vysledek, None, "int")
							else:
								print("Chyba: instrukce_sub - spatny typ - musi byt integer", file=sys.stderr)
								sys.exit(53) # TODO
						else:
							print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
							sys.exit(54) # TODO
					#druhy symbol je int
					elif symb3.attrib['type'] == 'int':
						tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame)
						cislo1 = string_to_cislo(tmp)
						cislo2 = string_to_cislo(symb3.text)
						vysledek = cislo1 - cislo2
						pridat_do_promenne(var.text[3:], var_frame, vysledek, None, "int")
					else:
						print("Chyba: instrukce_sub - spatny typ - musi byt integer", file=sys.stderr)
						sys.exit(53) # TODO
				# prvni symbol je var->string/bool
				else:
					print("Chyba: instrukce_sub - spatny typ - musi byt integer", file=sys.stderr)
					sys.exit(53) # TODO
			else:
				print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
				sys.exit(54) # TODO	
		# prvni symbol je primo integer
		elif symb2.attrib['type'] == 'int':
			if symb3.attrib['type'] == 'var':
				if is_declared(symb3.text[3:], symb3_frame) == 0:
					# prvni symbol je var->int
					if je_v_promenne_typ(symb3.text[3:], symb3_frame, "int") == 0:
						cislo1 = string_to_cislo(symb2.text)
						tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame)
						cislo2 = string_to_cislo(tmp)
						vysledek = cislo1 - cislo2
						pridat_do_promenne(var.text[3:], var_frame, vysledek, None, "int")
					else:
						print("Chyba: instrukce_sub - spatny typ - musi byt integer", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
					sys.exit(54) # TODO
			elif symb3.attrib['type'] == 'int':
				cislo1 = string_to_cislo(symb2.text)
				cislo2 = string_to_cislo(symb3.text)
				vysledek = cislo1 - cislo2
				pridat_do_promenne(var.text[3:], var_frame, vysledek, None, "int")	
			else:
				print("Chyba: instrukce_sub - spatny typ - musi byt integer", file=sys.stderr)
				sys.exit(53) # TODO
		# pro bool/string neni instrukce definovana
		else:
			print("Chyba: instrukce_sub - spatny typ - musi byt integer", file=sys.stderr)
			sys.exit(53) # TODO
	else:
		print("Chyba: Snazite se provest operaci SUB nad neexistujici promennou", file=sys.stderr)
		sys.exit(54) # TODO3
# TODO - symboly musi byt typu int, coz bych mel kontrolovat asi uz v prvnim behu
# TODO - muze byt symbol promenna, ktera obsahuje promennou typu int?
def instrukce_mul(instrukce):
	var = instrukce.find("arg1")
	symb2 = instrukce.find("arg2")
	symb3 = instrukce.find("arg3")

	# urceni ramce var
	if var.text[:3] == "GF@":
		var_frame = "GF"
	elif var.text[:3] == "LF@":	
		var_frame = "LF"
		if not zasobnik_volani:
			print("Chyba: zasobnik volani", file=sys.stderr)
			sys.exit(55) # TODO
	elif var.text[:3] == "TF@":
		var_frame = "TF"
		if temp_frame_defined == 0:
			print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
			sys.exit(55) # TODO
	else:
		print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
		sys.exit(45) # TODO

	if symb2.attrib['type'] == "var":
		if var.text[:3] == "GF@":
			symb2_frame = "GF"
		elif symb2.text[:3] == "LF@":	
			symb2_frame = "LF"
		elif symb2.text[:3] == "TF@":
			symb2_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
			sys.exit(45) # TODO

	if symb3.attrib['type'] == "var":
		if symb3.text[:3] == "GF@":
			symb3_frame = "GF"
		elif symb3.text[:3] == "LF@":	
			symb3_frame = "LF"
		elif symb3.text[:3] == "TF@":
			symb3_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
			sys.exit(45) # TODO

	if is_declared(var.text[3:],var_frame) == 0:
		if symb2.attrib['type'] == 'var':
			if is_declared(symb2.text[3:], symb2_frame) == 0:
				# prvni symbol je var->int
				if je_v_promenne_typ(symb2.text[3:], symb2_frame, "int") == 0:
					if symb3.attrib['type'] == 'var':
						if is_declared(symb3.text[3:], symb3_frame) == 0:
							# prvni symbol je var->int
							if je_v_promenne_typ(symb3.text[3:], symb3_frame, "int") == 0:
								tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
								cislo1 = string_to_cislo(tmp)
								tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
								cislo2 = string_to_cislo(gtmp)
								vysledek = cislo1 * cislo2
								pridat_do_promenne(var.text[3:], var_frame, vysledek, None, "int")
							else:
								print("Chyba: instrukce_mul - spatny typ - musi byt integer", file=sys.stderr)
								sys.exit(53) # TODO
						else:
							print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
							sys.exit(54) # TODO
					elif symb3.attrib['type'] == 'int':
						tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
						cislo1 = string_to_cislo(tmp)
						cislo2 = string_to_cislo(symb3.text)
						vysledek = cislo1 * cislo2
						pridat_do_promenne(var.text[3:], var_frame, vysledek, None, "int")
					else:
						print("Chyba: instrukce_mul - spatny typ - musi byt integer", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: instrukce_mul - spatny typ - musi byt integer", file=sys.stderr)
					sys.exit(53) # TODO
			else:
				print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
				sys.exit(54) # TODO
		elif symb2.attrib['type'] == 'int':
			if symb3.attrib['type'] == 'var':
				if is_declared(symb3.text[3:], symb3_frame) == 0:
					if je_v_promenne_typ(symb3.text[3:], symb3_frame, "int") == 0:
						cislo1 = string_to_cislo(symb2.text)
						tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
						cislo2 = string_to_cislo(tmp)
						vysledek = cislo1 * cislo2
						pridat_do_promenne(var.text[3:], var_frame, vysledek, None, "int")
					else:
						print("Chyba: instrukce_sub - spatny typ - musi byt integer", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
					sys.exit(54) # TODO
			elif symb3.attrib['type'] == 'int':
				cislo1 = string_to_cislo(symb2.text)
				cislo2 = string_to_cislo(symb3.text)
				vysledek = cislo1 * cislo2
				pridat_do_promenne(var.text[3:], var_frame, vysledek, None, "int")	
			else:
				print("Chyba: instrukce_sub - spatny typ - musi byt integer", file=sys.stderr)
				sys.exit(53) # TODO
		else:
			print("Chyba: instrukce_sub - spatny typ", file=sys.stderr)
			sys.exit(53) # TODO
	else:
		print("Chyba: Snazite se provest operaci SUB nad neexistujici promennou", file=sys.stderr)
		sys.exit(54) # TODO
def instrukce_idiv(instrukce):
	var = instrukce.find("arg1")
	symb2 = instrukce.find("arg2")
	symb3 = instrukce.find("arg3")

	# urceni ramce var
	if var.text[:3] == "GF@":
		var_frame = "GF"
	elif var.text[:3] == "LF@":	
		var_frame = "LF"
		if not zasobnik_volani:
			print("Chyba: zasobnik volani", file=sys.stderr)
			sys.exit(55) # TODO
	elif var.text[:3] == "TF@":
		var_frame = "TF"
		if temp_frame_defined == 0:
			print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
			sys.exit(55) # TODO
	else:
		print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
		sys.exit(46) # TODO

	if symb2.attrib['type'] == "var":
		if var.text[:3] == "GF@":
			symb2_frame = "GF"
		elif symb2.text[:3] == "LF@":	
			symb2_frame = "LF"
		elif symb2.text[:3] == "TF@":
			symb2_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
			sys.exit(46) # TODO

	if symb3.attrib['type'] == "var":
		if symb3.text[:3] == "GF@":
			symb3_frame = "GF"
		elif symb3.text[:3] == "LF@":	
			symb3_frame = "LF"
		elif symb3.text[:3] == "TF@":
			symb3_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
			sys.exit(46) # TODO

	if is_declared(var.text[3:],var_frame) == 0:
		if symb2.attrib['type'] == 'var':
			if is_declared(symb2.text[3:], symb2_frame) == 0:
				# prvni symbol je var->int
				if je_v_promenne_typ(symb2.text[3:], symb2_frame, "int") == 0:
					if symb3.attrib['type'] == 'var':
						if is_declared(symb3.text[3:], symb3_frame) == 0:
							if je_v_promenne_typ(symb3.text[3:], symb3_frame, "int") == 0:
								tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
								cislo1 = string_to_cislo(tmp)
								tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
								cislo2 = string_to_cislo(tmp)
								if cislo2 == 0:
									print("Chyba: Deleni nulou", file=sys.stderr)
									sys.exit(57)
								vysledek = cislo1 / cislo2
								vysledek = int(vysledek)
								pridat_do_promenne(var.text[3:], var_frame, vysledek, None, "int")
							else:
								print("Chyba: instrukce_mul - spatny typ - musi byt integer", file=sys.stderr)
								sys.exit(53) # TODO
						else:
							print("Chyba: Promenna neexistuje", file=sys.stderr)
							sys.exit(54) # TODO
					elif symb3.attrib['type'] == 'int':
						tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
						cislo1 = string_to_cislo(tmp)
						cislo2 = string_to_cislo(symb3.text)
						if cislo2 == 0:
							print("Chyba: Deleni nulou", file=sys.stderr)
							sys.exit(57)
						vysledek = cislo1 / cislo2							
						vysledek = int(vysledek)
						pridat_do_promenne(var.text[3:], var_frame, vysledek, None, "int")
					else:
						print("Chyba: instrukce_mul - spatny typ - musi byt integer", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: instrukce_mul - spatny typ - musi byt integer", file=sys.stderr)
					sys.exit(53) # TODO
			else:
				print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
				sys.exit(54) # TODO
		elif symb2.attrib['type'] == 'int':
			if symb3.attrib['type'] == 'var':
				if is_declared(symb3.text[3:], symb3_frame) == 0:
					# prvni symbol je var->int
					if je_v_promenne_typ(symb3.text[3:], symb3_frame, "int") == 0:	
						cislo1 = string_to_cislo(symb2.text)
						tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
						cislo2 = string_to_cislo(tmp)
						if cislo2 == 0:
							print("Chyba: Deleni nulou", file=sys.stderr)
							sys.exit(57)
						vysledek = cislo1 / cislo2
						vysledek = int(vysledek)
						pridat_do_promenne(var.text[3:], var_frame, vysledek, None, "int")
					else:
						print("Chyba: instrukce_sub - spatny typ - musi byt integer", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: Promenna nebyla deklaroava", file=sys.stderr)
					sys.exit(54) # TODO
			elif symb3.attrib['type'] == 'int':
				cislo1 = string_to_cislo(symb2.text)
				cislo2 = string_to_cislo(symb3.text)
				if cislo2 == 0:
					print("Chyba: Deleni nulou", file=sys.stderr)
					sys.exit(57)					
				vysledek = cislo1 / cislo2
				vysledek = int(vysledek)
				pridat_do_promenne(var.text[3:], var_frame, vysledek, None, "int")
			else:
				print("Chyba: instrukce_sub - spatny typ - musi byt integer", file=sys.stderr)
				sys.exit(53) # TODO
		else:
			print("Chyba: instrukce_sub - spatny typ", file=sys.stderr)
			sys.exit(53) # TODO
	else:
		print("Chyba: Snazite se provest operaci SUB nad neexistujici promennou", file=sys.stderr)
		sys.exit(54) # TODO
# TODO - zjistuju, ze kdyz muze byt int 000001 a bere se to jako 1, je to dobre?
# TODO string, bool
# TODO - LF TF
def instrukce_lt(instrukce):
	var = instrukce.find("arg1")
	symb2 = instrukce.find("arg2")
	symb3 = instrukce.find("arg3")

	# urceni ramce var
	if var.text[:3] == "GF@":
		var_frame = "GF"
	elif var.text[:3] == "LF@":	
		var_frame = "LF"
		if not zasobnik_volani:
			print("Chyba: zasobnik volani", file=sys.stderr)
			sys.exit(55) # TODO
	elif var.text[:3] == "TF@":
		var_frame = "TF"
		if temp_frame_defined == 0:
			print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
			sys.exit(55) # TODO
	else:
		print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
		sys.exit(47) # TODO

	if symb2.attrib['type'] == "var":
		if var.text[:3] == "GF@":
			symb2_frame = "GF"
		elif symb2.text[:3] == "LF@":	
			symb2_frame = "LF"
		elif symb2.text[:3] == "TF@":
			symb2_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
			sys.exit(47) # TODO

	if symb3.attrib['type'] == "var":
		if symb3.text[:3] == "GF@":
			symb3_frame = "GF"
		elif symb3.text[:3] == "LF@":	
			symb3_frame = "LF"
		elif symb3.text[:3] == "TF@":
			symb3_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
			sys.exit(47) # TODO

	# musime overit, ze je promenna deklarovana
	if is_declared(var.text[3:], var_frame) == 0:
		# symboly museji byt stejenho typu
		if symb2.attrib['type'] == symb3.attrib['type']:
			if symb2.attrib['type'] == 'int':
				cislo1 = string_to_cislo(symb2.text)
				cislo2 = string_to_cislo(symb3.text)
				if cislo1 < cislo2:
					# DO:
					# promenna = var
					# ramec_promenne = GF / LF / TF
					# Z:
					# hodnota = 16515 / sdfsf / true / var
					# ramec = GF/LF/TF/ None
					# typ_hodnoty = string/bool/int/None - nevime
					pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
				else:
					pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
			elif symb2.attrib['type'] == 'string':
				# TODO - porovnani retezcu dat do dokumentace, ze prazdnej retezec je ve slovniku an prvnim miste
				if symb2.text == "" or symb2.text is None:
					if symb3.text == "" or symb3.text is None:
						pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
					else:
						pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
				else:
					if symb2.text < symb3.text:
						pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
					else:
						pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
			elif symb2.attrib['type'] == 'bool':
				# TODO - muze byt i velkym pismem?
				if symb2.text == 'true':
					cislo1 = 1
				else:
					cislo1 = 0
				if symb3.text == 'true':
					cislo2 = 1
				else:
					cislo1 = 0
				if cislo1 < cislo2:
					pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
				else:
					pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
			elif symb2.attrib['type'] == 'var':
				if is_declared(symb2.text[3:], symb2_frame) == 0: # TODO - zkontrolovat uplne vsude, ze pokud pristupujeme k promenne, tak kontrolujem, jestli je definovana
					if is_declared(symb3.text[3:], symb3_frame) == 0:
						# oba symboly jsou promenne, ale jejich typ souhlasi
						typ1 = vrat_typ_promenne(symb2.text[3:], symb2_frame)
						typ2 = vrat_typ_promenne(symb3.text[3:], symb3_frame)
						if typ1 == typ2:
							if je_v_promenne_typ(symb2.text[3:], symb2_frame, "int") == 0:
								tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
								cislo1 = string_to_cislo(tmp)
								tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
								cislo2 = string_to_cislo(tmp)
								if cislo1 < cislo2:
									pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
								else:
									pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")									
							elif je_v_promenne_typ(symb2.text[3:], symb2_frame, "string") == 0:
								# TODO - porovnani retezcu dat do dokumentace, ze prazdnej retezec je ve slovniku an prvnim miste
								tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
								if tmp == "" or tmp is None:
									tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
									if tmp == "" or tmp is None:
										pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")	
									else:
										pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")	
								else:
									tmp1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
									tmp2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
									if tmp < tmp2:
										pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")	
									else:
										pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")										
							elif je_v_promenne_typ(symb2.text[3:], symb2_frame, "bool") == 0:
								tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
								# TODO - muze byt i velkym pismem?
								if tmp == 'true':
									cislo1 = 1
								else:
									cislo1 = 0
								tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame)
								if tmp == 'true':
									cislo2 = 1
								else:
									cislo1 = 0
								if cislo1 < cislo2:
									pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")	
								else:
									pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")										
							else:
								print("Chyba: Tady se nikdy nedostanu, je spatnej typ", file=sys.stderr)
								sys.exit(53) # TODO
						else:
							print("Chyba: promenna neexistuje..............", file=sys.stderr)
							sys.exit(54) # TODO	
					else:
						print("Chyba: promenna neexistuje", file=sys.stderr)
						sys.exit(54) # TODO	
				else:
					print("Chyba: promenna neexistuje", file=sys.stderr)
					sys.exit(54) # TODO

			else:
				print("Chyba: Tady se nikdy nedostanu", file=sys.stderr)
				sys.exit(47) # TODO
		# nejsou stejneho typu, nebo jsou oba symboly promenne
		# musme overit vnitrek
		else:
			# pokud nejsou stejneho typu, musime jeste overit, jestli se nejedna o promenne
			# to bychom museli porovnat jejich obsah
			if symb2.attrib['type'] == 'var':
				if is_declared(symb2.text[3:], symb2_frame) == 0: # TODO - zkontrolovat uplne vsude, ze pokud pristupujeme k promenne, tak kontrolujem, jestli je definovana
					typ1 = vrat_typ_promenne(symb2.text[3:], symb2_frame)
					if symb3.attrib['type'] != typ1:
						print("Chyba: funkce LT - symbooly nejsou stejneho typu", file=sys.stderr)
						sys.exit(53) # TODO
					elif symb3.attrib['type'] == 'int':
						tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
						cislo1 = string_to_cislo(tmp)
						cislo2 = string_to_cislo(symb3.text)
						if cislo1 < cislo2:
							pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")	
						else:
							pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")	
					elif symb3.attrib['type'] == 'string':
						tmp1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
						# TODO - porovnani retezcu dat do dokumentace, ze prazdnej retezec je ve slovniku an prvnim miste
						if tmp1 == "" or tmp1 is None:
							if symb3.text == "" or symb3.text is None:
								pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
							else:
								pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
						else:
							if tmp1 < symb3.text:
								pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
							else:
								pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
					elif symb3.attrib['type'] == 'bool':
						# TODO - muze byt i velkym pismem?
						tmp1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
						if tmp1 == 'true':
							cislo1 = 1
						else:
							cislo1 = 0
						if symb3.text == 'true':
							cislo2 = 1
						else:
							cislo1 = 0
						if cislo1 < cislo2:
							pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
						else:
							pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")	
					else:
						print("Chyba: Tady se nikdy nedostanu", file=sys.stderr)
						sys.exit(49) # TODO
				else:
					print("Chyba: promenna neexistuje", file=sys.stderr)
					sys.exit(54) # TODO
			elif symb3.attrib['type'] == 'var':
				if is_declared(symb3.text[3:], symb3_frame) == 0: # TODO - zkontrolovat uplne vsude, ze pokud pristupujeme k promenne, tak kontrolujem, jestli je definovana
					typ2 = vrat_typ_promenne(symb3.text[3:], symb3_frame)
					if symb2.attrib['type'] != typ2:
						print("Chyba: funkce LT - symbooly nejsou stejneho typu", file=sys.stderr)
						sys.exit(53) # TODO
					elif symb2.attrib['type'] == 'int':
						tmp2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
						cislo1 = string_to_cislo(symb2.text)
						cislo2 = string_to_cislo(tmp2)
						if cislo1 < cislo2:
							pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")	
						else:
							pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")	
					elif symb2.attrib['type'] == 'string':
						tmp2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
						# TODO - porovnani retezcu dat do dokumentace, ze prazdnej retezec je ve slovniku an prvnim miste
						if symb2.text == "" or symb2.text is None:
							if tmp2 == "" or tmp2 is None:
								pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")	
							else:
								pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")	
						else:
							if symb2.text < tmp2:
								pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")	
							else:
								pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")	
					elif symb3.attrib['type'] == 'bool':
						tmp2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
						# TODO - muze byt i velkym pismem?
						if symb2.text == 'true':
							cislo1 = 1
						else:
							cislo1 = 0
						if tmp2 == 'true':
							cislo2 = 1
						else:
							cislo1 = 0
						if cislo1 < cislo2:
							pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")	
						else:
							pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")		
					else:
						print("Chyba: Tady se nikdy nedostanu", file=sys.stderr)
						sys.exit(49) # TODO
				else:
					print("Chyba: promenna neexistuje", file=sys.stderr)
					sys.exit(54) # TODO
			else:
				print("Chyba: funkce LT - symboly nejsou stejneho typu", file=sys.stderr)
				sys.exit(53) # TODO
	else:
		print("Chyba: Snazite se provest operaci SUB nad neexistujici promennou", file=sys.stderr)
		sys.exit(54) # TODO
# TODO string, bool
# TODO - LF TF
def instrukce_gt(instrukce):
	var = instrukce.find("arg1")
	symb2 = instrukce.find("arg2")
	symb3 = instrukce.find("arg3")

	# urceni ramce var
	if var.text[:3] == "GF@":
		var_frame = "GF"
	elif var.text[:3] == "LF@":	
		var_frame = "LF"
		if not zasobnik_volani:
			print("Chyba: zasobnik volani", file=sys.stderr)
			sys.exit(55) # TODO
	elif var.text[:3] == "TF@":
		var_frame = "TF"
		if temp_frame_defined == 0:
			print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
			sys.exit(55) # TODO
	else:
		print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
		sys.exit(50) # TODO

	if symb2.attrib['type'] == "var":
		if var.text[:3] == "GF@":
			symb2_frame = "GF"
		elif symb2.text[:3] == "LF@":	
			symb2_frame = "LF"
		elif symb2.text[:3] == "TF@":
			symb2_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
			sys.exit(50) # TODO

	if symb3.attrib['type'] == "var":
		if symb3.text[:3] == "GF@":
			symb3_frame = "GF"
		elif symb3.text[:3] == "LF@":	
			symb3_frame = "LF"
		elif symb3.text[:3] == "TF@":
			symb3_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
			sys.exit(50) # TODO

	# musime overit, ze je promenna deklarovana
	if is_declared(var.text[3:],var_frame) == 0:
		# symboly museji byt stejenho typu
		if symb2.attrib['type'] == symb3.attrib['type']:
			if symb2.attrib['type'] == 'int':
				cislo1 = string_to_cislo(symb2.text)
				cislo2 = string_to_cislo(symb3.text)
				if cislo1 > cislo2:
					pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
				else:
					pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
			elif symb2.attrib['type'] == 'string':
				# TODO - porovnani retezcu dat do dokumentace, ze prazdnej retezec je ve slovniku an prvnim miste
				if symb3.text == "" or symb3.text is None:
					if symb2.text == "" or symb2.text is None:
						pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
					else:
						pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
				else:
					if symb2.text > symb3.text:
						pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
					else:
						pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
			elif symb2.attrib['type'] == 'bool':
				# TODO - muze byt i velkym pismem?
				if symb2.text == 'true':
					cislo1 = 1
				else:
					cislo1 = 0
				if symb3.text == 'true':
					cislo2 = 1
				else:
					cislo1 = 0
				if cislo1 > cislo2:
					pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
				else:
					pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
			elif symb2.attrib['type'] == 'var':
				if is_declared(symb2.text[3:],symb2_frame) == 0: # TODO - zkontrolovat uplne vsude, ze pokud pristupujeme k promenne, tak kontrolujem, jestli je definovana
					if is_declared(symb3.text[3:],symb3_frame) == 0:
						# oba symboly jsou promenne, ale jejich typ souhlasi
						typ1 = vrat_typ_promenne(symb2.text[3:], symb2_frame)
						typ2 = vrat_typ_promenne(symb3.text[3:], symb3_frame)
						if typ1 == typ2:
							if je_v_promenne_typ(symb2.text[3:], symb2_frame, "int") == 0:
								tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
								cislo1 = string_to_cislo(tmp)
								tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
								cislo2 = string_to_cislo(tmp)
								if cislo1 > cislo2:
									pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
								else:
									pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")								
							elif je_v_promenne_typ(symb2.text[3:], symb2_frame, "string") == 0:
								# TODO - porovnani retezcu dat do dokumentace, ze prazdnej retezec je ve slovniku an prvnim miste
								tmp1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
								tmp2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
								if tmp2 == "" or tmp2 is None:
									if tmp1 == "" or tmp1 is None:
										pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
									else:
										pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
								else:
									if tmp1 > tmp2:
										pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
									else:
										pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")								
							elif je_v_promenne_typ(symb2.text[3:], symb2_frame, "bool") == 0:
								# TODO - muze byt i velkym pismem?
								tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
								if tmp == 'true':
									cislo1 = 1
								else:
									cislo1 = 0
								tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
								if tmp == 'true':
									cislo2 = 1
								else:
									cislo1 = 0
								if cislo1 > cislo2:
									pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
								else:
									pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")									
							else:
								print("Chyba: Tady se nikdy nedostanu", file=sys.stderr)
								sys.exit(50) # TODO
					else:
						print("Chyba: promenna neexistuje", file=sys.stderr)
						sys.exit(54) # TODO	
				else:
					print("Chyba: promenna neexistuje", file=sys.stderr)
					sys.exit(54) # TODO

			else:
				print("Chyba: Tady se nikdy nedostanu", file=sys.stderr)
				sys.exit(50) # TODO
		# nejsou stejneho typu, nebo jsou oba symboly promenne
		# musme overit vnitrek
		else:
			# pokud nejsou stejneho typu, musime jeste overit, jestli se nejedna o promenne
			# to bychom museli porovnat jejich obsah
			if symb2.attrib['type'] == 'var':
				if is_declared(symb2.text[3:],symb2_frame) == 0: # TODO - zkontrolovat uplne vsude, ze pokud pristupujeme k promenne, tak kontrolujem, jestli je definovana
					typ1 = vrat_typ_promenne(symb2.text[3:], symb2_frame)
					if symb3.attrib['type'] != typ1:
						print("Chyba: funkce LT - symbooly nejsou stejneho typu", file=sys.stderr)
						sys.exit(53) # TODO
					elif symb3.attrib['type'] == 'int':
						tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
						cislo1 = string_to_cislo(tmp)
						cislo2 = string_to_cislo(symb3.text)
						if cislo1 > cislo2:
							pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
						else:
							pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
					elif symb3.attrib['type'] == 'string':
						tmp1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
						# TODO - porovnani retezcu dat do dokumentace, ze prazdnej retezec je ve slovniku an prvnim miste
						if symb3.text == "" or symb3.text is None:
							if tmp1 == "" or tmp1 is None:
								pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
							else:
								pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
						else:
							if tmp1 > symb3.text:
								pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
							else:
								pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
					elif symb3.attrib['type'] == 'bool':
						# TODO - muze byt i velkym pismem?
						tmp1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
						if tmp1 == 'true':
							cislo1 = 1
						else:
							cislo1 = 0
						if symb3.text == 'true':
							cislo2 = 1
						else:
							cislo1 = 0
						if cislo1 > cislo2:
							pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
						else:
							pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
					else:
						print("Chyba: Tady se nikdy nedostanu", file=sys.stderr)
						sys.exit(50) # TODO
				else:
					print("Chyba: promenna neexistuje", file=sys.stderr)
					sys.exit(54) # TODO
			elif symb3.attrib['type'] == 'var':
				# TODO - zkontrolovat, ze je u vsech is_declared predan ramec pres promennou
				if is_declared(symb3.text[3:], symb3_frame) == 0: # TODO - zkontrolovat uplne vsude, ze pokud pristupujeme k promenne, tak kontrolujem, jestli je definovana
					typ2 = vrat_typ_promenne(symb3.text[3:], symb3_frame)
					if symb2.attrib['type'] != typ2:
						print("Chyba: funkce LT - symbooly nejsou stejneho typu", file=sys.stderr)
						sys.exit(53) # TODO
					elif symb2.attrib['type'] == 'int':
						tmp2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
						cislo1 = string_to_cislo(symb2.text)
						cislo2 = string_to_cislo(tmp2)
						if cislo1 > cislo2:
							pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
						else:
							pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
					elif symb2.attrib['type'] == 'string':
						# TODO - porovnani retezcu dat do dokumentace, ze prazdnej retezec je ve slovniku an prvnim miste
						tmp2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
						if tmp2 == "" or tmp2 is None:
							if symb2.text == "" or symb2.text is None:
								pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
							else:
								pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
						else:
							if symb2.text > tmp2:
								pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
							else:
								pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
					elif symb3.attrib['type'] == 'bool':
						tmp2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
						# TODO - muze byt i velkym pismem?
						if symb2.text == 'true':
							cislo1 = 1
						else:
							cislo1 = 0
						if tmp2 == 'true':
							cislo2 = 1
						else:
							cislo1 = 0
						if cislo1 > cislo2:
							pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
						else:
							pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
					else:
						print("Chyba: Tady se nikdy nedostanu", file=sys.stderr)
						sys.exit(50) # TODO
				else:
					print("Chyba: promenna neexistuje", file=sys.stderr)
					sys.exit(54) # TODO
			else:
				print("Chyba: funkce LT - symboly nejsou stejneho typu", file=sys.stderr)
				sys.exit(53) # TODO
	else:
		print("Chyba: Snazite se provest operaci SUB nad neexistujici promennou", file=sys.stderr)
		sys.exit(54) # TODO
# TODO string, bool
# TODO - LF TF
def instrukce_eq(instrukce):
	var = instrukce.find("arg1")
	symb2 = instrukce.find("arg2")
	symb3 = instrukce.find("arg3")
	# urceni ramce var
	if var.text[:3] == "GF@":
		var_frame = "GF"
	elif var.text[:3] == "LF@":	
		var_frame = "LF"
		if not zasobnik_volani:
			print("Chyba: zasobnik volani", file=sys.stderr)
			sys.exit(55) # TODO
	elif var.text[:3] == "TF@":
		var_frame = "TF"
		if temp_frame_defined == 0:
			print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
			sys.exit(55) # TODO
	else:
		print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
		sys.exit(50) # TODO

	if symb2.attrib['type'] == "var":
		if var.text[:3] == "GF@":
			symb2_frame = "GF"
		elif symb2.text[:3] == "LF@":	
			symb2_frame = "LF"
		elif symb2.text[:3] == "TF@":
			symb2_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
			sys.exit(50) # TODO

	if symb3.attrib['type'] == "var":
		if symb3.text[:3] == "GF@":
			symb3_frame = "GF"
		elif symb3.text[:3] == "LF@":	
			symb3_frame = "LF"
		elif symb3.text[:3] == "TF@":
			symb3_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
			sys.exit(50) # TODO

	# musime overit, ze je promenna deklarovana
	if is_declared(var.text[3:],var_frame) == 0:
		# symboly museji byt stejenho typu
		if symb2.attrib['type'] == symb3.attrib['type']:
			if symb2.attrib['type'] == 'int':
				cislo1 = string_to_cislo(symb2.text)
				cislo2 = string_to_cislo(symb3.text)
				if cislo1 == cislo2:
					pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
				else:
					pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
			elif symb2.attrib['type'] == 'string':
				# TODO - porovnani retezcu dat do dokumentace, ze prazdnej retezec je ve slovniku an prvnim miste
				if symb3.text == "" or symb3.text is None:
					if symb2.text == "" or symb2.text is None:
						pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
					else:
						pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
				# TODO - naseldujici elif neni v predchozich a asi by tam mel byt
				elif symb2.text == "" or symb2.text is None:
					if symb3.text == "" or symb3.text is None:
						pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
					else:
						pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
				else:
					if symb2.text == symb3.text:
						pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
					else:
						pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
			elif symb2.attrib['type'] == 'bool':
				# TODO - muze byt i velkym pismem?
				if symb2.text == 'true':
					cislo1 = 1
				else:
					cislo1 = 0
				if symb3.text == 'true':
					cislo2 = 1
				else:
					cislo1 = 0
				if cislo1 == cislo2:
					pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
				else:
					pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
			elif symb2.attrib['type'] == 'var':
				if is_declared(symb2.text[3:],symb2_frame) == 0: # TODO - zkontrolovat uplne vsude, ze pokud pristupujeme k promenne, tak kontrolujem, jestli je definovana
					if is_declared(symb3.text[3:],symb3_frame) == 0:
						typ1 = vrat_typ_promenne(symb2.text[3:], symb2_frame)
						typ2 = vrat_typ_promenne(symb3.text[3:], symb3_frame)
						# oba symboly jsou promenne, ale jejich typ souhlasi
						if typ1 == typ2:
							if je_v_promenne_typ(symb2.text[3:], symb2_frame, "int") == 0:
								tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
								cislo1 = string_to_cislo(tmp)
								tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
								cislo2 = string_to_cislo(tmp)
								if cislo1 == cislo2:
									pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
								else:
									pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")									
							elif je_v_promenne_typ(symb2.text[3:], symb2_frame, "string") == 0:
								# TODO - porovnani retezcu dat do dokumentace, ze prazdnej retezec je ve slovniku an prvnim miste
								tmp1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
								tmp2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
								if tmp2 == "" or tmp2 is None:
									if tmp1 == "" or tmp1 is None:
										pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
									else:
										pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
								elif tmp1 == "" or tmp1 is None:
									if tmp2 == "" or tmp2 is None:
										pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
									else:
										pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
								else:
									if tmp1 == tmp2:
										pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
									else:
										pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")									
							elif je_v_promenne_typ(symb2.text[3:], symb2_frame, "bool") == 0:
								# TODO - muze byt i velkym pismem?
								tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
								if tmp == 'true':
									cislo1 = 1
								else:
									cislo1 = 0
								tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
								if tmp == 'true':
									cislo2 = 1
								else:
									cislo1 = 0
								if cislo1 == cislo2:
									pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
								else:
									pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")									
							else:
								print("Chyba: Tady se nikdy nedostanu", file=sys.stderr)
								sys.exit(50) # TODO
					else:
						print("Chyba: promenna neexistuje", file=sys.stderr)
						sys.exit(54) # TODO	
				else:
					print("Chyba: promenna neexistuje", file=sys.stderr)
					sys.exit(54) # TODO

			else:
				print("Chyba: Tady se nikdy nedostanu", file=sys.stderr)
				sys.exit(50) # TODO
		# nejsou stejneho typu, nebo jsou oba symboly promenne
		# musme overit vnitrek
		else:
			# pokud nejsou stejneho typu, musime jeste overit, jestli se nejedna o promenne
			# to bychom museli porovnat jejich obsah
			if symb2.attrib['type'] == 'var':
				if is_declared(symb2.text[3:],symb2_frame) == 0: # TODO - zkontrolovat uplne vsude, ze pokud pristupujeme k promenne, tak kontrolujem, jestli je definovana
					typ1 = vrat_typ_promenne(symb2.text[3:], symb2_frame)
					if symb3.attrib['type'] != typ1:
						print("Chyba: funkce LT - symbooly nejsou stejneho typu", file=sys.stderr)
						sys.exit(53) # TODO
					elif symb3.attrib['type'] == 'int':
						tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
						cislo1 = string_to_cislo(tmp)
						cislo2 = string_to_cislo(symb3.text)
						if cislo1 == cislo2:
							pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
						else:
							pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
					elif symb3.attrib['type'] == 'string':
						tmp1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame)  
						# TODO - porovnani retezcu dat do dokumentace, ze prazdnej retezec je ve slovniku an prvnim miste
						if tmp1 == "" or tmp1 is None:
							if symb3.text == "" or symb3.text is None:
								pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
							else:
								pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
						elif symb3.text == "" or symb3.text is None:
							if tmp1 == "" or tmp1 is None:
								pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
							else:
								pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
						else:
							if tmp1 == symb3.text:
								pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
							else:
								pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
					elif symb3.attrib['type'] == 'bool':
						tmp1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
						# TODO - muze byt i velkym pismem?
						if tmp1 == 'true':
							cislo1 = 1
						else:
							cislo1 = 0
						if symb3.text == 'true':
							cislo2 = 1
						else:
							cislo1 = 0
						if cislo1 == cislo2:
							pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
						else:
							pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")	
					else:
						print("Chyba: Tady se nikdy nedostanu", file=sys.stderr)
						sys.exit(45) # TODO
				else:
					print("Chyba: promenna neexistuje", file=sys.stderr)
					sys.exit(54) # TODO
			elif symb3.attrib['type'] == 'var':
				if is_declared(symb3.text[3:],symb3_frame) == 0: # TODO - zkontrolovat uplne vsude, ze pokud pristupujeme k promenne, tak kontrolujem, jestli je definovana
					typ2 = vrat_typ_promenne(symb3.text[3:], symb3_frame)
					if symb2.attrib['type'] != typ2:
						print("Chyba: funkce LT - symbooly nejsou stejneho typu", file=sys.stderr)
						sys.exit(53) # TODO
					elif symb2.attrib['type'] == 'int':
						tmp2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
						cislo1 = string_to_cislo(symb2.text)
						cislo2 = string_to_cislo(tmp2)
						if cislo1 == cislo2:
							pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
						else:
							pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
					elif symb2.attrib['type'] == 'string':
						tmp2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame)
						# TODO - porovnani retezcu dat do dokumentace, ze prazdnej retezec je ve slovniku an prvnim miste
						if tmp2 == "" or tmp2 is None:
							if symb2.text == "" or symb2.text is None:
								pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
							else:
								pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
						elif symb2.text == "" or symb2.text is None:
							if tmp2 == "" or tmp2 is None:
								pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
							else:
								pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
						else:
							if symb2.text == tmp2:
								pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
							else:
								pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
					elif symb3.attrib['type'] == 'bool':
						tmp2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame)
						# TODO - muze byt i velkym pismem?
						if symb2.text == 'true':
							cislo1 = 1
						else:
							cislo1 = 0
						if tmp2 == 'true':
							cislo2 = 1
						else:
							cislo1 = 0
						if cislo1 == cislo2:
							pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
						else:
							pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")	
					else:
						print("Chyba: Tady se nikdy nedostanu", file=sys.stderr)
						sys.exit(45) # TODO
				else:
					print("Chyba: promenna neexistuje", file=sys.stderr)
					sys.exit(54) # TODO
			else:
				print("Chyba: funkce LT - symboly nejsou stejneho typu", file=sys.stderr)
				sys.exit(53) # TODO
	else:
		print("Chyba: Snazite se provest operaci SUB nad neexistujici promennou", file=sys.stderr)
		sys.exit(54) # TODO

def instrukce_and(instrukce):
	var = instrukce.find("arg1")
	symb2 = instrukce.find("arg2")
	symb3 = instrukce.find("arg3")
	# promenna musi byt nejakeho ramce
	if var.text[:3] == "GF@":
		var_frame = "GF"
	elif var.text[:3] == "LF@":
		var_frame = "LF"
		if not zasobnik_volani:
			print("Chyba: zasobnik volani", file=sys.stderr)
			sys.exit(55) # TODO
	elif var.text[:3] == "TF@":
		var_frame = "TF"
		if temp_frame_defined == 0:
			print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
			sys.exit(55) # TODO
	else:
		print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
		sys.exit(45) # TODO

	if symb2.attrib['type'] == "var":
		if symb2.text[:3] == "GF@":
			symb2_frame = "GF"
		elif symb2.text[:3] == "LF@":
			symb2_frame = "LF"
		elif symb2.text[:3] == "TF@":
			symb2_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
			sys.exit(45) # TODO

	if symb3.attrib['type'] == "var":
		if symb3.text[:3] == "GF@":
			symb3_frame = "GF"
		elif symb3.text[:3] == "LF@":
			symb3_frame = "LF"
		elif symb3.text[:3] == "TF@":
			symb3_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
			sys.exit(45) # TODO

	if is_declared(var.text[3:],var_frame) == 0:
		if symb2.attrib['type'] == "var":
			if is_declared(symb2.text[3:],symb2_frame) == 0:
				if je_v_promenne_typ(symb2.text[3:], symb2_frame, "bool") == 0:
					if symb3.attrib['type'] == "var":
						if is_declared(symb3.text[3:],symb3_frame) == 0:
							if je_v_promenne_typ(symb3.text[3:], symb3_frame, "bool") == 0:
								bool1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame)
								bool2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame)
								if bool1 == "true" and bool2 == "true":
									# DO:
									# promenna = var
									# ramec_promenne = GF / LF / TF
									# Z:
									# hodnota = 16515 / sdfsf / true / var
									# ramec = GF/LF/TF/ None - pokud neni promenna 
									# typ_hodnoty = string/bool/int/None - nevime
									pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
								else:
									pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
							else:
								print("Chyba: Vyzadujeme bool", file=sys.stderr)
								sys.exit(53) # TODO
						else:
							print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
							sys.exit(54) # TODO		
					elif symb3.attrib['type'] == "bool":
						bool1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame)
						bool2 = symb3.text
						if bool1 == "true" and bool2 == "true":
							pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
						else:
							pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
					else:
						print("Chyba: Vyzadujeme bool", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: Vyzadujeme bool", file=sys.stderr)
					sys.exit(53) # TODO
			else:
				print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
				sys.exit(54) # TODO
		elif symb2.attrib['type'] == "bool":
			if symb3.attrib['type'] == "var": 
				if is_declared(symb3.text[3:],symb3_frame) == 0:
					if je_v_promenne_typ(symb3.text[3:], symb3_frame, "bool") == 0:
						bool1 = symb2.text
						bool2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame)
						if bool1 == "true" and bool2 == "true":
							pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
						else:
							pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
					else:
						print("Chyba: Vyzaduje se bool", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
					sys.exit(53) # TODO
			elif symb3.attrib['type'] == "bool": 
				bool1 = symb2.text
				bool2 = symb3.text
				if bool1 == "true" and bool2 == "true":
					pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
				else:
					pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
			else:
				print("Chyba: Vyzaduje se bool", file=sys.stderr)
				sys.exit(53) # TODO
		else:
			print("Chyba: Vyzaduje se bool", file=sys.stderr)
			sys.exit(53) # TODO
	else:
		print("Chyba: promenna nebyla deklarovana", file=sys.stderr)
		sys.exit(54) # TODO
def instrukce_or(instrukce):
	var = instrukce.find("arg1")
	symb2 = instrukce.find("arg2")
	symb3 = instrukce.find("arg3")
	# promenna musi byt nejakeho ramce
	if var.text[:3] == "GF@":
		var_frame = "GF"
	elif var.text[:3] == "LF@":
		var_frame = "LF"
		if not zasobnik_volani:
			print("Chyba: zasobnik volani", file=sys.stderr)
			sys.exit(55) # TODO
	elif var.text[:3] == "TF@":
		var_frame = "TF"
		if temp_frame_defined == 0:
			print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
			sys.exit(55) # TODO
	else:
		print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
		sys.exit(46) # TODO

	if symb2.attrib['type'] == "var":
		if symb2.text[:3] == "GF@":
			symb2_frame = "GF"
		elif symb2.text[:3] == "LF@":
			symb2_frame = "LF"
		elif symb2.text[:3] == "TF@":
			symb2_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
			sys.exit(46) # TODO

	if symb3.attrib['type'] == "var":
		if symb3.text[:3] == "GF@":
			symb3_frame = "GF"
		elif symb3.text[:3] == "LF@":
			symb3_frame = "LF"
		elif symb3.text[:3] == "TF@":
			symb3_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
			sys.exit(46) # TODO

	if is_declared(var.text[3:],var_frame) == 0:
		if symb2.attrib['type'] == "var":
			if is_declared(symb2.text[3:],symb2_frame) == 0:
				if je_v_promenne_typ(symb2.text[3:], symb2_frame, "bool") == 0:
					if symb3.attrib['type'] == "var":
						if is_declared(symb3.text[3:],symb3_frame) == 0:
							if je_v_promenne_typ(symb3.text[3:], symb3_frame, "bool") == 0:
								bool1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame)
								bool2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame)
								if bool1 == "false" and bool2 == "false":
									# DO:
									# promenna = var
									# ramec_promenne = GF / LF / TF
									# Z:
									# hodnota = 16515 / sdfsf / true / var
									# ramec = GF/LF/TF/ None - pokud neni promenna 
									# typ_hodnoty = string/bool/int/None - nevime
									pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
								else:
									pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
							else:
								print("Chyba: Vyzadujeme bool", file=sys.stderr)
								sys.exit(53) # TODO
						else:
							print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
							sys.exit(54) # TODO		
					elif symb3.attrib['type'] == "bool":
						bool1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame)
						bool2 = symb3.text
						if bool1 == "false" and bool2 == "false":
							pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
						else:
							pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
					else:
						print("Chyba: Vyzadujeme bool", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: Vyzadujeme bool", file=sys.stderr)
					sys.exit(53) # TODO
			else:
				print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
				sys.exit(54) # TODO
		elif symb2.attrib['type'] == "bool":
			if symb3.attrib['type'] == "var": 
				if is_declared(symb3.text[3:],symb3_frame) == 0:
					if je_v_promenne_typ(symb3.text[3:], symb3_frame, "bool") == 0:
						bool1 = symb2.text
						bool2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame)
						if bool1 == "false" and bool2 == "false":
							pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
						else:
							pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
					else:
						print("Chyba: Vyzaduje se bool", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
					sys.exit(54) # TODO
			elif symb3.attrib['type'] == "bool": 
				bool1 = symb2.text
				bool2 = symb3.text
				if bool1 == "false" and bool2 == "false":
					pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
				else:
					pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
			else:
				print("Chyba: Vyzaduje se bool", file=sys.stderr)
				sys.exit(53) # TODO
		else:
			print("Chyba: Vyzaduje se bool", file=sys.stderr)
			sys.exit(53) # TODO
	else:
		print("Chyba: promenna nebyla deklarovana", file=sys.stderr)
		sys.exit(54) # TODO
def instrukce_not(instrukce):
	var = instrukce.find("arg1")
	symb2 = instrukce.find("arg2")
	# promenna musi byt nejakeho ramce
	if var.text[:3] == "GF@":
		var_frame = "GF"
	elif var.text[:3] == "LF@":
		var_frame = "LF"
		if not zasobnik_volani:
			print("Chyba: zasobnik volani", file=sys.stderr)
			sys.exit(55) # TODO
	elif var.text[:3] == "TF@":
		var_frame = "TF"
		if temp_frame_defined == 0:
			print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
			sys.exit(55) # TODO
	else:
		print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
		sys.exit(46) # TODO

	if symb2.attrib['type'] == "var":
		if symb2.text[:3] == "GF@":
			symb2_frame = "GF"
		elif symb2.text[:3] == "LF@":
			symb2_frame = "LF"
		elif symb2.text[:3] == "TF@":
			symb2_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
			sys.exit(46) # TODO

	if is_declared(var.text[3:],var_frame) == 0:
		if symb2.attrib['type'] == "var":
			if is_declared(symb2.text[3:],symb2_frame) == 0:
				if je_v_promenne_typ(symb2.text[3:], symb2_frame, "bool") == 0:
					bool1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame)
					if bool1 == "true":
						pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")	
					else:
						pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
				else:
					print("Chyba: Vyzadujeme bool", file=sys.stderr)
					sys.exit(53) # TODO
			else:
				print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
				sys.exit(54) # TODO
		elif symb2.attrib['type'] == "bool":
			bool1 = symb2.text
			if bool1 == "true":
				pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")	
			else:
				pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
		else:
			print("Chyba: Vyzaduje se bool", file=sys.stderr)
			sys.exit(53) # TODO
	else:
		print("Chyba: promenna nebyla deklarovana", file=sys.stderr)
		sys.exit(54) # TODO
def instrukce_int2char(instrukce):
	var = instrukce.find("arg1")
	symb = instrukce.find("arg2")

	# promenna musi byt nejakeho ramce
	if var.text[:3] == "GF@":
		var_frame = "GF"
	elif var.text[:3] == "LF@":
		var_frame = "LF"
		if not zasobnik_volani:
			print("Chyba: zasobnik volani", file=sys.stderr)
			sys.exit(55) # TODO
	elif var.text[:3] == "TF@":
		var_frame = "TF"
		if temp_frame_defined == 0:
			print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
			sys.exit(55) # TODO
	else:
		print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
		sys.exit(43) # TODO

	if symb.attrib['type'] == "var":
		if symb.text[:3] == "GF@":
			symb_frame = "GF"
		elif symb.text[:3] == "LF@":
			symb_frame = "LF"
		elif symb.text[:3] == "TF@":
			symb_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
			sys.exit(43) # TODO

	if is_declared(var.text[3:],var_frame) == 0:
		if symb.attrib['type'] == "int":
			cislo = string_to_cislo(symb.text)
			if cislo > 1114111: # TODO - je to opravdu tak?
				print("Chyba: Cislo nesmi byt vetsi nez 1114111", file=sys.stderr)
				sys.exit(58) # TODO
			elif cislo < 0:
				print("Chyba: Cislo musi byt vetsi nez nula", file=sys.stderr)
				sys.exit(58) # TODO
			else:
				cislo = chr(cislo)
				pridat_do_promenne(var.text[3:], var_frame, cislo, None, "string")
		elif symb.attrib['type'] == "var":
			if is_declared(symb.text[3:],symb_frame) == 0:
				if je_v_promenne_typ(symb.text[3:], symb_frame, "int") == 0:
					tmp = vrat_hodnotu_promenne(symb.text[3:], symb_frame) 
					cislo = string_to_cislo(tmp)
					if cislo > 1114111:
						print("Chyba: Cislo nesmi byt vetsi nez 1114111", file=sys.stderr)
						sys.exit(58) # TODO
					elif cislo < 0:
						print("Chyba: Cislo musi byt vetsi nez nula", file=sys.stderr)
						sys.exit(58) # TODO
					else:
						cislo = chr(cislo)
						pridat_do_promenne(var.text[3:], var_frame, cislo, None, "string")
				else:
					print("Chyba: Je vyzadovan integer", file=sys.stderr)
					sys.exit(53) # TODO
			else:
				print("Chyba: Promenna neexistuje", file=sys.stderr)
				sys.exit(54) # TODO
		else:
			print("Chyba: funkce int2char - je potreba, aby bylo cislo int", file=sys.stderr)
			sys.exit(53) # TODO
	else:
		print("Chyba: Promenna nebyla dekalrovana", file=sys.stderr)
		sys.exit(54) # TODO
def instrukce_stri2int(instrukce):
	var = instrukce.find("arg1")
	symb2 = instrukce.find("arg2")
	symb3 = instrukce.find("arg3")

	# urceni ramce var
	if var.text[:3] == "GF@":
		var_frame = "GF"
	elif var.text[:3] == "LF@":	
		var_frame = "LF"
		if not zasobnik_volani:
			print("Chyba: zasobnik volani", file=sys.stderr)
			sys.exit(55) # TODO
	elif var.text[:3] == "TF@":
		var_frame = "TF"
		if temp_frame_defined == 0:
			print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
			sys.exit(55) # TODO
	else:
		print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
		sys.exit(44) # TODO

	if symb2.attrib['type'] == "var":
		if var.text[:3] == "GF@":
			symb2_frame = "GF"
		elif symb2.text[:3] == "LF@":	
			symb2_frame = "LF"
		elif symb2.text[:3] == "TF@":
			symb2_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
			sys.exit(44) # TODO

	if symb3.attrib['type'] == "var":
		if symb3.text[:3] == "GF@":
			symb3_frame = "GF"
		elif symb3.text[:3] == "LF@":	
			symb3_frame = "LF"
		elif symb3.text[:3] == "TF@":
			symb3_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
			sys.exit(44) # TODO

	if is_declared(var.text[3:],var_frame) == 0:
		if symb2.attrib['type'] == "string":
			if symb3.attrib['type'] == "int":
				index = string_to_cislo(symb3.text)
				if index < 0:
					print("Chyba: index musi byt vetsi nez nula", file=sys.stderr)
					sys.exit(58) # TODO
				elif index > len(symb2.text)-1:
					print("Chyba: index nesmi byt vetsi nez je delka stringu", file=sys.stderr)
					sys.exit(58) # TODO
				else:
					tmp = ord(symb2.text[index])
					pridat_do_promenne(var.text[3:], var_frame, tmp, None, "int")
			elif symb3.attrib['type'] == "var":
				if is_declared(symb3.text[3:],symb3_frame) == 0:
					if je_v_promenne_typ(symb3.text[3:], symb3_frame, "int") == 0:
						tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
						index = string_to_cislo(tmp)
						if index < 0:
							print("Chyba: index musi byt vetsi nez nula", file=sys.stderr)
							sys.exit(58) # TODO
						elif index > len(symb2.text)-1:
							print("Chyba: index nesmi byt vetsi nez je delka stringu", file=sys.stderr)
							sys.exit(58) # TODO
						else:
							tmp = ord(symb2.text[index])
							pridat_do_promenne(var.text[3:], var_frame, tmp, None, "int")
					else:
						print("Chyba: Ocekavam int", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: Promenna nebyla dekalrovana", file=sys.stderr)
					sys.exit(54) # TODO
			else:
				print("Chyba: funkce stri2int - neni int", file=sys.stderr)
				sys.exit(53) # TODO
		elif symb2.attrib['type'] == "var":
			if is_declared(var.text[3:],symb2_frame) == 0:
				if je_v_promenne_typ(symb2.text[3:], symb2_frame, "string") == 0:
					if symb3.attrib['type'] == "int":
						index = string_to_cislo(symb3.text)
						tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
						if index < 0:
							print("Chyba: index musi byt vetsi nez nula", file=sys.stderr)
							sys.exit(58) # TODO
						elif index > len(tmp)-1:
							print("Chyba: index nesmi byt vetsi nez je delka stringu", file=sys.stderr)
							sys.exit(58) # TODO
						else:
							tmp2 = ord(tmp[index])
							pridat_do_promenne(var.text[3:], var_frame, tmp2, None, "int")
							# print(ord(tmp[index]))
					elif symb3.attrib['type'] == "var":
						if is_declared(symb3.text[3:],symb3_frame) == 0:
							if je_v_promenne_typ(symb3.text[3:], symb3_frame, "int") == 0:
								tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 	
								tmp2 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
								index = string_to_cislo(tmp)
								if index < 0:
									print("Chyba: index musi byt vetsi nez nula", file=sys.stderr)
									sys.exit(58) # TODO
								elif index > len(tmp2)-1:
									print("Chyba: index nesmi byt vetsi nez je delka stringu", file=sys.stderr)
									sys.exit(58) # TODO
								else:
									tmp3 = ord(tmp2[index])
									pridat_do_promenne(var.text[3:], var_frame, tmp3, None, "int")
									# print(ord(tmp2[index]))
							else:
								print("Chyba: ocekavan int", file=sys.stderr)
								sys.exit(53) # TODO
						else:
							print("Chyba: promenna nedeklarovana", file=sys.stderr)
							sys.exit(54) # TODO
					else:
						print("Chyba: Ocekavam int", file=sys.stderr)
						sys.exit(53) # TODO	
				else:
					print("Chyba: Ocekavam string", file=sys.stderr)
					sys.exit(53) # TODO
			else:
				print("Chyba: Promenna nebyla dekalrovana", file=sys.stderr)
				sys.exit(54) # TODO
		else:
			print("Chyba: funkce stri2int - neni string", file=sys.stderr)
			sys.exit(53) # TODO
	else:
		print("Chyba: Promenna nebyla dekalrovana", file=sys.stderr)
		sys.exit(54) # TODO
# TODO - preteceni?
def instrukce_read(instrukce):
	var = instrukce.find("arg1")
	typ = instrukce.find("arg2")

	# urceni ramce var
	if var.text[:3] == "GF@":
		var_frame = "GF"
	elif var.text[:3] == "LF@":	
		var_frame = "LF"
		if not zasobnik_volani:
			print("Chyba: zasobnik volani", file=sys.stderr)
			sys.exit(55) # TODO
	elif var.text[:3] == "TF@":
		var_frame = "TF"
		if temp_frame_defined == 0:
			print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
			sys.exit(55) # TODO
	else:
		print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
		sys.exit(43) # TODO


	if is_declared(var.text[3:],var_frame) == 0:
		retezec = input()
		if typ.text == 'bool':
			if retezec.lower() == 'true':
				pridat_do_promenne(var.text[3:], var_frame, "true", None, "bool")
			else:
				pridat_do_promenne(var.text[3:], var_frame, "false", None, "bool")
		elif typ.text == 'string':
			# TODO - osetreni
			pridat_do_promenne(var.text[3:], var_frame, retezec, None, "string")
		elif typ.text == 'int':
			try:
				tmp = int(retezec)
				pridat_do_promenne(var.text[3:], var_frame, tmp, None, "int")
			except:
				pridat_do_promenne(var.text[3:], var_frame, 0, None, "int")
		else:
			print("Chyba: neexistujici typ", file=sys.stderr)
			sys.exit(53) # TODO
	else:
		print("Chyba: Neexistuje promenna", file=sys.stderr)
		sys.exit(54) # TODO
def instrukce_write(instrukce):
	symb = instrukce.find("arg1")

	if symb.attrib['type'] == "var":
		if symb.text[:3] == "GF@":
			symb_frame = "GF"
		elif symb.text[:3] == "LF@":
			symb_frame = "LF"
		elif symb.text[:3] == "TF@":
			symb_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
			sys.exit(43) # TODO


	if symb.attrib['type'] == 'var':
		if je_v_promenne_typ(symb.text[3:], symb_frame, "string") == 0:
			tmp = vrat_hodnotu_promenne(symb.text[3:], symb_frame) 
			if tmp is None or tmp is "":
				print("")
			elif symb.attrib['type'] is "":
				print("") # TODO - funguje to takhle spravne? je to tady k necemu? :D .. je to nesmysl
				return
			elif symb.text is None:
				print("") # TODO - funguje to takhle spravne?
				return
			else:
				tmp = check_escape(tmp)
				print(tmp)
		elif je_v_promenne_typ(symb.text[3:], symb_frame, "int") == 0:
			tmp = vrat_hodnotu_promenne(symb.text[3:], symb_frame) 
			tmp = int(tmp)
			print(tmp)
		elif je_v_promenne_typ(symb.text[3:], symb_frame, "bool") == 0:
			tmp = vrat_hodnotu_promenne(symb.text[3:], symb_frame)
			print(tmp)
		else:
			print("Chyba: 1 tady by se to dostat nemelo", file=sys.stderr)
			sys.exit(53) # TODO
	elif symb.attrib['type'] == 'string':
		if symb.text is None or symb.text == "":
			print("")
		else:
			tmp = check_escape(symb.text)
			print(tmp) # TODO - predelat sekvence na nejaky znak
	elif symb.attrib['type'] == 'int':
		tmp = int(symb.text)
		print(tmp)
	elif symb.attrib['type'] == 'bool':
		print(symb.text)
	else:
		print("Chyba: 2 tady by se to dostat nemelo", file=sys.stderr)
		sys.exit(43) # TODO
def instrukce_strlen(instrukce):
	var = instrukce.find("arg1")
	symb = instrukce.find("arg2")

	# promenna musi byt nejakeho ramce
	if var.text[:3] == "GF@":
		var_frame = "GF"
	elif var.text[:3] == "LF@":
		var_frame = "LF"
		if not zasobnik_volani:
			print("Chyba: zasobnik volani", file=sys.stderr)
			sys.exit(55) # TODO
	elif var.text[:3] == "TF@":
		var_frame = "TF"
		if temp_frame_defined == 0:
			print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
			sys.exit(55) # TODO
	else:
		print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
		sys.exit(43) # TODO

	if symb.attrib['type'] == "var":
		if symb.text[:3] == "GF@":
			symb_frame = "GF"
		elif symb.text[:3] == "LF@":
			symb_frame = "LF"
		elif symb.text[:3] == "TF@":
			symb_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
			sys.exit(43) # TODO

	if var.attrib['type'] == 'var':
		if is_declared(var.text[3:], var_frame) == 0:
			if symb.attrib['type'] == 'var':
				if is_declared(symb.text[3:], symb_frame) == 0:
					if je_v_promenne_typ(symb.text[3:], symb_frame, "string") == 0:
						if symb.text is None:
							delka = 0
						else:
							tmp = vrat_hodnotu_promenne(symb.text[3:], symb_frame) 
							delka = len(tmp)
						pridat_do_promenne(var.text[3:], var_frame, delka, None, "int")
					else:
						print("Chyba: musi byt string", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
					sys.exit(54) # TODO
			elif symb.attrib['type'] == 'string':
				if symb.text is None:
					delka = 0
				else:
					delka = len(symb.text)
				pridat_do_promenne(var.text[3:], var_frame, delka, None, "int")
			else:
				print("Chyba: Symbol musi byt string", file=sys.stderr)
				sys.exit(53) # TODO
		else:
			print("Chyba: Promenna musi byt deklarovana", file=sys.stderr)
			sys.exit(54) # TODO
	else:
		print("Chyba: musi byt promenna", file=sys.stderr)
		sys.exit(53) # TODO
def instrukce_getchar(instrukce):
	var = instrukce.find("arg1")
	symb2 = instrukce.find("arg2")
	symb3 = instrukce.find("arg3")
	# urceni ramce var
	if var.text[:3] == "GF@":
		var_frame = "GF"
	elif var.text[:3] == "LF@":	
		var_frame = "LF"
		if not zasobnik_volani:
			print("Chyba: zasobnik volani", file=sys.stderr)
			sys.exit(55) # TODO
	elif var.text[:3] == "TF@":
		var_frame = "TF"
		if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
	else:
		print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
		sys.exit(42) # TODO

	if symb2.attrib['type'] == 'var':
		# urceni ramce var
		if symb2.text[:3] == "GF@":
			symb2_frame = "GF"
		elif symb2.text[:3] == "LF@":	
			symb2_frame = "LF"
		elif symb2.text[:3] == "TF@":
			symb2_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
			sys.exit(42) # TODO

	if symb3.attrib['type'] == 'var':
		# urceni ramce var
		if symb3.text[:3] == "GF@":
			symb3_frame = "GF"
		elif symb3.text[:3] == "LF@":	
			symb3_frame = "LF"
		elif symb3.text[:3] == "TF@":
			symb3_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
			sys.exit(42) # TODO	

	if var.attrib['type'] == 'var':
		if is_declared(var.text[3:], var_frame) == 0:
			if symb2.attrib['type'] == 'var':
				if is_declared(symb2.text[3:],symb2_frame) == 0:
					if je_v_promenne_typ(symb2.text[3:], symb2_frame, "string") == 0:
						# oba promenne
						if symb3.attrib['type'] == 'var':
							if is_declared(symb3.text[3:],symb3_frame) == 0:
								if je_v_promenne_typ(symb3.text[3:], symb3_frame, "int") == 0:
									tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
									tmp2 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
									index = int(tmp)
									if tmp2 is None:
										delka = 0
									else:
										delka = len(tmp2)
									if index < 0:
										print("Chyba: integer musi byt vetsi nez nula", file=sys.stderr)
										sys.exit(58) # TODO
									elif index >= delka:
										print("Chyba: mimo rozsah", file=sys.stderr)
										sys.exit(58) # TODO
									else:
										znak = tmp2[index]
										pridat_do_promenne(var.text[3:], var_frame, znak, None, "string")
								else:
									print("Chyba: ocekavam int", file=sys.stderr)
									sys.exit(53) # TODO
							else:
								print("Chyba: promenna neni deklarovana", file=sys.stderr)
								sys.exit(54) # TODO
						# prvni promenna, druhy primo integer
						elif symb3.attrib['type'] == 'int':
							index = int(symb3.text)
							tmp1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
							tmp2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame)
							if tmp1 is None:
								delka = 0
							else:
								delka = len(tmp1)
							if index < 0:
								print("Chyba: integer musi byt vetsi nez nula", file=sys.stderr)
								sys.exit(58) # TODO
							elif index >= delka:
								print("Chyba: mimo rozsah", file=sys.stderr)
								sys.exit(58) # TODO
							else:
								znak = tmp1[index]
								pridat_do_promenne(var.text[3:], var_frame, znak, None, "string")						
						else:
							print("Chyba: ocekavam int", file=sys.stderr)
							sys.exit(53) # TODO
					else:
						print("Chyba: ocekavam string", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: promenna neni deklarovana", file=sys.stderr)
					sys.exit(54) # TODO
			elif symb2.attrib['type'] == 'string':
				if symb3.attrib['type'] == 'var':
					if is_declared(symb3.text[3:],symb3_frame) == 0:
						if je_v_promenne_typ(symb3.text[3:], symb3_frame, "int") == 0:
							tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
							index = int(tmp)
							if symb2.text is None:
								delka = 0
							else:
								delka = len(symb2.text)
							if index < 0:
								print("Chyba: integer musi byt vetsi nez nula", file=sys.stderr)
								sys.exit(58) # TODO
							elif index >= delka:
								print("Chyba: mimo rozsah", file=sys.stderr)
								sys.exit(58) # TODO
							else:
								znak = symb2.text[index]
								pridat_do_promenne(var.text[3:], var_frame, znak, None, "string")							
						else:
							print("Chyba: ocekavam int", file=sys.stderr)
							sys.exit(53) # TODO
					else:
						print("Chyba: promenna neni deklarovana", file=sys.stderr)
						sys.exit(54) # TODO
				if symb3.attrib['type'] == 'int':
					index = int(symb3.text)
					if symb2.text is None:
						delka = 0
					else:
						delka = len(symb2.text)
					if index < 0:
						print("Chyba: integer musi byt vetsi nez nula", file=sys.stderr)
						sys.exit(58) # TODO
					elif index >= delka:
						print("Chyba: mimo rozsah", file=sys.stderr)
						sys.exit(58) # TODO
					else:
						znak = symb2.text[index]
						pridat_do_promenne(var.text[3:], var_frame, znak, None, "string")					
				else:
					print("Chyba: ocekavam int", file=sys.stderr)
					sys.exit(53) # TODO
			else:
				print("Chyba: ocekavam string", file=sys.stderr)
				sys.exit(53) # TODO
		else:
			print("Chyba: promenna neni deklarovana", file=sys.stderr)
			sys.exit(54) # TODO
	else:
		print("Chyba: musi byt promenna", file=sys.stderr)
		sys.exit(53) # TODO
def instrukce_concat(instrukce):
	var = instrukce.find("arg1")
	symb2 = instrukce.find("arg2")
	symb3 = instrukce.find("arg3")
	# promenna musi byt nejakeho ramce
	if var.text[:3] == "GF@":
		var_frame = "GF"
	elif var.text[:3] == "LF@":
		var_frame = "LF"
		if not zasobnik_volani:
			print("Chyba: zasobnik volani", file=sys.stderr)
			sys.exit(55) # TODO
	elif var.text[:3] == "TF@":
		var_frame = "TF"
		if temp_frame_defined == 0:
			print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
			sys.exit(55) # TODO
	else:
		print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
		sys.exit(41) # TODO

	if symb2.attrib['type'] == "var":
		if symb2.text[:3] == "GF@":
			symb2_frame = "GF"
		elif symb2.text[:3] == "LF@":
			symb2_frame = "LF"
		elif symb2.text[:3] == "TF@":
			symb2_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
			sys.exit(41) # TODO

	if symb3.attrib['type'] == "var":
		if symb3.text[:3] == "GF@":
			symb3_frame = "GF"
		elif symb3.text[:3] == "LF@":
			symb3_frame = "LF"
		elif symb3.text[:3] == "TF@":
			symb3_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
			sys.exit(41) # TODO

	# vysledek musime ukladat do promenne
	if var.attrib['type'] == 'var':
		# kontrola, jestli je promenna deklarovana
		if is_declared(var.text[3:],var_frame) == 0:
			# prvni symbol je var->?
			if symb2.attrib['type'] == 'var':
				if is_declared(symb2.text[3:],symb2_frame) == 0:
					# prvni symbol je var->?  druhy symbol je var->?
					if symb3.attrib['type'] == 'var':
						if is_declared(symb3.text[3:],symb3_frame) == 0:
							# musime zkontrolovat, jakeho typu jsou promenne
							typ1 = vrat_typ_promenne(symb2.text[3:], symb2_frame)
							typ2 = vrat_typ_promenne(symb3.text[3:], symb3_frame)
							if typ1 == 'string' and typ2 == 'string':
								tmp1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
								tmp2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
								if tmp1 is None:
									if tmp2 is None:
										vysledek = "" + ""
									else:
										vysledek = "" + tmp2
								elif tmp2 is None:
									vysledek = tmp1 + ""
								else:
									vysledek = tmp1 + tmp2
								pridat_do_promenne(var.text[3:], var_frame, vysledek, None, "string")
							else:
								print("Chyba: Musi byt string", file=sys.stderr)
								sys.exit(53) # TODO	
						else:
							print("Chyba: promenna nebyla deklarovana", file=sys.stderr)
							sys.exit(54) # TODO	
					# prvni symbol je var->? druhy symbol je string	
					elif symb3.attrib['type'] == 'string':
						tmp1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame)
						if tmp1 is None:
							if symb3.text is None:
								vysledek = "" + ""
							else:
								vysledek =  "" + symb3.text # TODO - co kdyz bude prvni ok a prazndej az druhej
						elif symb3.text is None:
							vysledek = tmp1 + ""
						else:
							vysledek =  tmp1 + symb3.text
						pridat_do_promenne(var.text[3:], var_frame, vysledek, None, "string")	
					else:
						print("Chyba: Spatnej format", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: promenna nebyla deklarovana", file=sys.stderr)
					sys.exit(54) # TODO
			elif symb2.attrib['type'] == 'string':
				if symb3.attrib['type'] == 'var':
					if is_declared(symb3.text[3:],symb3_frame) == 0:
						# TODO co kdyz bude jineho ramce?
						if je_v_promenne_typ(symb3.text[3:], symb3_frame, "string") == 0:
							# druhy je none
							tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
							if tmp is None:
								# prvni je none
								if symb2.text is None:
									vysledek = "" + ""
								# prvni ok, druhy none
								else:
									vysledek =  symb2.text + ""
							# prvni je none
							elif symb2.text is None:
								vysledek = "" + tmp
							else:
								vysledek =  symb2.text + tmp
							pridat_do_promenne(var.text[3:], var_frame, vysledek, None, "string")				
						else:
							print("Chyba: musi byt string", file=sys.stderr)
							sys.exit(53) # TODO
					else:
						print("Chyba: promenna nebyla deklarovana", file=sys.stderr)
						sys.exit(54) # TODO
				elif symb3.attrib['type'] == 'string':
					if symb2.text is None:
						if symb3.text is None:
							vysledek =  "" + ""
						else:
							vysledek =  "" + symb3.text
					elif symb3.text is None:
						vysledek =  symb2.text + ""
					else:
						vysledek =  symb2.text + symb3.text
					pridat_do_promenne(var.text[3:], var_frame, vysledek, None, "string")
				else:
					print("Chyba: ", file=sys.stderr)
					sys.exit(53) # TODO
			else:
				print("Chyba: ", file=sys.stderr)
				sys.exit(53) # TODO
		else:
			print("Chyba: promenna nebyla deklarovana", file=sys.stderr)
			sys.exit(54) # TODO
	else:
		print("Chyba: ", file=sys.stderr)
		sys.exit(53) # TODO

def instrukce_setchar(instrukce):
	var = instrukce.find("arg1")
	symb2 = instrukce.find("arg2")
	symb3 = instrukce.find("arg3")
	# urceni ramce var
	if var.text[:3] == "GF@":
		var_frame = "GF"
	elif var.text[:3] == "LF@":	
		var_frame = "LF"
		if not zasobnik_volani:
			print("Chyba: zasobnik volani", file=sys.stderr)
			sys.exit(55) # TODO
	elif var.text[:3] == "TF@":
		var_frame = "TF"
		if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
	else:
		print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
		sys.exit(42) # TODO

	if symb2.attrib['type'] == 'var':
		# urceni ramce var
		if symb2.text[:3] == "GF@":
			symb2_frame = "GF"
		elif symb2.text[:3] == "LF@":	
			symb2_frame = "LF"
		elif symb2.text[:3] == "TF@":
			symb2_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
			sys.exit(42) # TODO

	if symb3.attrib['type'] == 'var':
		# urceni ramce var
		if symb3.text[:3] == "GF@":
			symb3_frame = "GF"
		elif symb3.text[:3] == "LF@":	
			symb3_frame = "LF"
		elif symb3.text[:3] == "TF@":
			symb3_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostta nemelo", file=sys.stderr)
			sys.exit(42) # TODO	

	# promenna, ze ktere bereme string
	if var.attrib['type'] == 'var':
		# musi byt deklarovan
		if is_declared(var.text[3:], var_frame) == 0:
			# musi obsahovat string
			if je_v_promenne_typ(var.text[3:], var_frame, "string") == 0:
				if symb2.attrib['type'] == 'var':
					if is_declared(symb2.text[3:],symb2_frame) == 0:
						if je_v_promenne_typ(symb2.text[3:], symb2_frame, "int") == 0:
							if symb3.attrib['type'] == 'var':
								if is_declared(symb3.text[3:],symb3_frame) == 0:
									if je_v_promenne_typ(symb3.text[3:], symb3_frame, "string") == 0:
										tmp1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
										tmp2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
										if tmp2 is None:
											print("Chyba: prazdny retezec", file=sys.stderr)
											sys.exit(58) # TODO
										else:
											tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
											tmp2 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
											retezec = vrat_hodnotu_promenne(var.text[3:], var_frame) 
											index = int(tmp2)
											# delka retezewce
											delka = len(retezec)
											if index < 0:
												print("Chyba: integer musi byt vetsi nez nula", file=sys.stderr)
												sys.exit(58) # TODO
											elif index >= delka:
												print("Chyba: mimo rozsah", file=sys.stderr)
												sys.exit(58) # TODO
											else:
												s = list(retezec)
												s[index] = tmp[0]
												retezec = "".join(s)
												pridat_do_promenne(var.text[3:], var_frame, retezec, None, "string")									
									else:
										print("Chyba: Spatnej typ", file=sys.stderr)
										sys.exit(53) # TODO
								else:
									print("Chyba: promenna nebyla deklarovana", file=sys.stderr)
									sys.exit(54) # TODO
							elif symb3.attrib['type'] == 'string':	
								tmp1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
								tmp2 = symb3.text
								if tmp2 is None:
									print("Chyba: prazdny retezec", file=sys.stderr)
									sys.exit(58) # TODO
								else:
									tmp = symb3.text 
									tmp2 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
									retezec = vrat_hodnotu_promenne(var.text[3:], var_frame) 
									index = int(tmp2)
									# delka retezewce
									delka = len(retezec)
									if index < 0:
										print("Chyba: integer musi byt vetsi nez nula", file=sys.stderr)
										sys.exit(58) # TODO
									elif index >= delka:
										print("Chyba: mimo rozsah", file=sys.stderr)
										sys.exit(58) # TODO
									else:
										s = list(retezec)
										s[index] = tmp[0]
										retezec = "".join(s)
										pridat_do_promenne(var.text[3:], var_frame, retezec, None, "string")	
							else:
								print("Chyba: Spatnej typ", file=sys.stderr)
								sys.exit(53) # TODO							
						else:
							print("Chyba: Spatnej typ", file=sys.stderr)
							sys.exit(53) # TODO
					else:
						print("Chyba: promenna nebyla deklarovana", file=sys.stderr)
						sys.exit(54) # TODO
				elif symb2.attrib['type'] == 'int':
					if symb3.attrib['type'] == 'var':
						if is_declared(symb3.text[3:], symb3_frame) == 0:
							if je_v_promenne_typ(symb3.text[3:], symb3_frame, "string") == 0:
								tmp1 = symb2.text
								tmp2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
								if tmp2 is None:
									print("Chyba: prazdny retezec", file=sys.stderr)
									sys.exit(58) # TODO
								else:
									tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
									tmp2 = symb2.text
									retezec = vrat_hodnotu_promenne(var.text[3:], var_frame) 
									index = int(tmp2)
									# delka retezewce
									delka = len(retezec)
									if index < 0:
										print("Chyba: integer musi byt vetsi nez nula", file=sys.stderr)
										sys.exit(58) # TODO
									elif index >= delka:
										print("Chyba: mimo rozsah", file=sys.stderr)
										sys.exit(58) # TODO
									else:
										s = list(retezec)
										s[index] = tmp[0]
										retezec = "".join(s)										
										pridat_do_promenne(var.text[3:], var_frame, retezec, None, "string")									
							else:
								print("Chyba: Spatnej typ", file=sys.stderr)
								sys.exit(53) # TODO
						else:
							print("Chyba: promenna nebyla deklarovana", file=sys.stderr)
							sys.exit(54) # TODO
					elif symb3.attrib['type'] == 'string':	
						tmp1 = symb2.text
						tmp2 = symb3.text
						if tmp2 is None:
							print("Chyba: prazdny retezec", file=sys.stderr)
							sys.exit(58) # TODO
						else:
							tmp = symb3.text
							tmp2 = symb2.text
							retezec = vrat_hodnotu_promenne(var.text[3:], var_frame) 
							index = int(tmp2)
							# delka retezewce
							delka = len(retezec)
							if index < 0:
								print("Chyba: integer musi byt vetsi nez nula", file=sys.stderr)
								sys.exit(58) # TODO
							elif index >= delka:
								print("Chyba: mimo rozsah", file=sys.stderr)
								sys.exit(58) # TODO
							else:
								s = list(retezec)
								s[index] = tmp[0]
								retezec = "".join(s)
								pridat_do_promenne(var.text[3:], var_frame, retezec, None, "string")	
					else:
						print("Chyba: Spatnej typ", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: Spatnej typ", file=sys.stderr)
					sys.exit(53) # TODO
			else:
				print("Chyba: Spatnej typ", file=sys.stderr)
				sys.exit(53) # TODO
		else:
			print("Chyba: promenna nebyyla deklarovana", file=sys.stderr)
			sys.exit(53) # TODO
	else:
		print("Chyba: musi byt promenna", file=sys.stderr)
		sys.exit(53) # TODO		

# tahle instrukce netusim, jestli funguje spravne
def instrukce_type(instrukce):
	for child in instrukce:
		if child.tag == "arg1":
				if child.attrib['type'] == "var":
					# promenna musi byt nejakeho ramce
					if child.text[:3] == "GF@":
						child_frame = "GF"
					elif child.text[:3] == "LF@":
						child_frame = "LF"
					elif child.text[:3] == "TF@":
						child_frame = "TF"
						if temp_frame_defined == 0:
							print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
							sys.exit(55) # TODO
					else:
						print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
						sys.exit(41) # TODO
				else:
					print("Chyba: spatnej typ", file=sys.stderr)
					sys.exit(53) # TODO
				if is_declared(child.text[3:],child_frame) == 0:
					if instrukce.find("arg2").attrib['type'] == "var":
						tmp = instrukce.find("arg2").text
						# promenna musi byt nejakeho ramce
						if tmp[:3] == "GF@":
							tmpp_frame = "GF"
						elif tmp[:3] == "LF@":
							tmpp_frame = "LF"
						elif tmp[:3] == "TF@":
							tmpp_frame = "TF"
							if temp_frame_defined == 0:
								print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
								sys.exit(55) # TODO
						else:
							print("Chyba: Tady by se to nikdy dostat nemelo - spatny ramec", file=sys.stderr)
							sys.exit(41) # TODO

						if is_declared(tmp[3:], tmpp_frame) == 0:
							tmp2 = vrat_typ_promenne(tmp[3:], tmpp_frame)
							tmp = vrat_hodnotu_promenne(tmp[3:], tmpp_frame)
							pridat_do_promenne(child.text[3:], child_frame, tmp2, None, "string")	
							# global_frame[child.text[3:]] = global_frame_types[tmp[3:]] 
							# global_frame_types[child.text[3:]] = "string"
						else:
							print("Chyba: Snazite se provest operaci TYPE nad promennou, ktera v ramci neexistuje", file=sys.stderr)
							sys.exit(54) # TODO
					else:
						if instrukce.find("arg2").attrib['type'] == "string":
							tmp =  "string"
							pridat_do_promenne(child.text[3:], child_frame, tmp, None, "string")
							# global_frame[child.text[3:]] = instrukce.find("arg2").text
							# global_frame_types[child.text[3:]] = "string"
						elif instrukce.find("arg2").attrib['type'] == "int":
							tmp =  "int"
							pridat_do_promenne(child.text[3:], child_frame, tmp, None, "string")
							# global_frame[child.text[3:]] = instrukce.find("arg2").text
							# global_frame_types[child.text[3:]] = "string"
						elif instrukce.find("arg2").attrib['type'] == "bool":
							tmp =  "bool"
							pridat_do_promenne(child.text[3:], child_frame, tmp, None, "string")
							# global_frame[child.text[3:]] = instrukce.find("arg2").text
							# global_frame_types[child.text[3:]] = "string"
						else:
							print("Chyba: ", file=sys.stderr)
							print("-------------------------------\n", file=sys.stderr)
							sys.exit(53) # TODO
				else:
					print("Chyba: Snazite se provest operaci TYPE nad promennou, ktera v ramci neexistuje", file=sys.stderr)
					sys.exit(54) # TODO
		elif child.tag == "arg2":
			continue
		else:
			print("Chyba: Sem se to nesmi dostat", file=sys.stderr)
			sys.exit(40) # TODO
def label_exist(label):
	try:
		label_list[label]
		return 0
	except:
		return 1
def instrukce_labell(instrukce):
	label = instrukce.find("arg1")
	if label.attrib['type'] != 'label':
		print("Chyba: spatny typ", file=sys.stderr)
		sys.exit(53) # TODO
	if label_exist(label.text) == 1:
		label_list[label.text] = int(instrukce.attrib['order'])+1
	# label jiz existuje a nsazime se vytvorit novy
	else:
		print("Chyba: Snazite se vytvorit jiz existujici label", file=sys.stderr)
		sys.exit(52) # TODO
def instrukce_jump(instrukce, root):
	jump = 0
	label = instrukce.find("arg1")
	if label.attrib['type'] != 'label':
		print("Chyba: spatny typ", file=sys.stderr)
		sys.exit(53) # TODO
	if label_exist(label.text) == 0:
		# v pripade, ze je label na posledni instrukci, tak nefunguje spravne
		# tahle podminak by to mela osetrit
		if int(label_list[label.text]) == len(root)+1:
			#ukoncime program bez chyby
			sys.exit(0)
		a = 0
		for i in range(int(label_list[label.text]), len(root)+1):
			if a == 1:
				break
			for instruction in root:
				if int(instruction.attrib['order']) == i:
					a = automat(instruction, root)
					jump = 1 # znaci, se doslo ke skoku a bude se muset ukoncit predchozi loop
					if a == 1:
						break
					else:
						continue
	else:
		print("Chyba: Snazite se skocit na neexistujici label", file=sys.stderr)
		sys.exit(52) # TODO
	if jump == 1:
		return 1
	else:
		return 0
def instrukce_jumpifeq(instrukce, root):
	label = instrukce.find("arg1")
	symb2 = instrukce.find("arg2")
	symb3 = instrukce.find("arg3")

	if label.attrib['type'] != 'label':
		print("Chyba: spatny typ", file=sys.stderr)
		sys.exit(53) # TODO

	if symb2.attrib['type'] == "var":
		if symb2.text[:3] == "GF@":
			symb2_frame = "GF"
		elif symb2.text[:3] == "LF@":
			symb2_frame = "LF"
		elif symb2.text[:3] == "TF@":
			symb2_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
			sys.exit(41) # TODO

	if symb3.attrib['type'] == "var":
		if symb3.text[:3] == "GF@":
			symb3_frame = "GF"
		elif symb3.text[:3] == "LF@":
			symb3_frame = "LF"
		elif symb3.text[:3] == "TF@":
			symb3_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
			sys.exit(41) # TODO	

	# nejprve zkontrolujeme, zda existuje label, na ktery chceme skocit
	if label_exist(label.text) == 0:
		# pokud je prvni symbol promenna
		# musime zjistit, co se v promenne nachazi za typ
		if symb2.attrib['type'] == 'var':
			if is_declared(symb2.text[3:], symb2_frame) == 0:
				# TODO - musime zkontrolovat, jestli pormenna existuje
				# pokud je i druhy symbol promenna
				# musime zase zjistit, co se v promenne nachazi za typ
				if symb3.attrib['type'] == 'var':
					if is_declared(symb3.text[3:], symb3_frame) == 0:
						# pokud se typ symbolu1 a symbolu2 nerovnaji, musi skoncit chybou
						typ1 = vrat_typ_promenne(symb2.text[3:], symb2_frame)
						typ2 = vrat_typ_promenne(symb3.text[3:], symb3_frame)
						if typ1 != typ2:
							print("Chyba: nemozne", file=sys.stderr)
							sys.exit(53) # TODO
						else:
							tmp1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
							tmp2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
							# pokud jsou typu int
							if je_v_promenne_typ(symb2.text[3:], symb2_frame, "int") == 0:
								if int(tmp2) == int(tmp1):
									jump = instrukce_jump(instrukce, root)
									if jump == 1:
										return 1
									else:
										return 0
								else:
									return
							# pro zbytek to muzeme udelat najednou
							else:
								if tmp2 == tmp1:
									jump = instrukce_jump(instrukce, root)
									if jump == 1:
										return 1
									else:
										return 0
								else:
									return
					else:
						print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
						sys.exit(54) # TODO
				# pokud je druhy symbol integet
				elif symb3.attrib['type'] == 'int':
					# musime porovnat, jestli jsou oba symboly stejneho typu
					typ1 = vrat_typ_promenne(symb2.text[3:], symb2_frame)
					if typ1 != 'int':
						print("Chyba: Neodpovidaji typy - nemuzeme porovnat", file=sys.stderr)
						sys.exit(53) # TODO
					tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame)
					tmp = int(tmp)
					if int(symb3.text) == tmp:
						jump = instrukce_jump(instrukce, root)
						if jump == 1:
							return 1
						else:
							return 0
					else:
						return
				# pokud je druhy symbol typu bool
				elif symb3.attrib['type'] == 'bool':
					# musime porovnat, jestli jsou oba symboly stejneho typu
					typ1 = vrat_typ_promenne(symb2.text[3:], symb2_frame)
					if typ1 != 'bool':
						print("Chyba: Neodpovidaji typy - nemuzeme porovnat", file=sys.stderr)
						sys.exit(53) # TODO
					tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame)
					if symb3.text == tmp:
						jump = instrukce_jump(instrukce, root)
						if jump == 1:
							return 1
						else:
							return 0
					else:
						return
				# pokud je druhy symbol typu string
				elif symb3.attrib['type'] == 'string':
					typ1 = vrat_typ_promenne(symb2.text[3:], symb2_frame)
					# musime porovnat, jestli jsou oba symboly stejneho typu
					if typ1 != 'string':
						print("Chyba: Neodpovidaji typy - nemuzeme porovnat", file=sys.stderr)
						sys.exit(53) # TODO
					tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame)
					if symb3.text == tmp:
						jump = instrukce_jump(instrukce, root)
						if jump == 1:
							return 1
						else:
							return 0
					else:
						return
				else:
					print("Chyba: nemozne", file=sys.stderr)
					sys.exit(53) # TODO
			else:
				print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
				sys.exit(54) # TODO
		# pokud je prvni symbol primo string
		# musime overit co je ten druhy
		elif symb2.attrib['type'] == 'string':
			if symb3.attrib['type'] == 'var':
				if is_declared(symb3.text[3:], symb3_frame) == 0:
					# musi byt string
					if je_v_promenne_typ(symb3.text[3:], symb3_frame, "string") == 0:
						tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame)
						if symb2.text == tmp:
							jump = instrukce_jump(instrukce, root)
							if jump == 1:
								return 1
							else:
								return 0
						else:
							return
					else:
						print("Chyba: Neodpovidaji typy - nemuzeme porovnat", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
					sys.exit(54) # TODO
			elif symb3.attrib['type'] == 'string':
				if symb2.text == symb3.text:
					jump = instrukce_jump(instrukce, root)
					if jump == 1:
						return 1
					else:
						return 0
				else:
					return
			else:
				print("Chyba: Neodpovidaji typy - nemuzeme porovnat", file=sys.stderr)
				sys.exit(53) # TODO
		elif symb2.attrib['type'] == 'int':
			if symb3.attrib['type'] == 'var':
				if is_declared(symb3.text[3:], symb3_frame) == 0:
					if je_v_promenne_typ(symb3.text[3:], symb3_frame, "int") == 0:
						tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame)
						tmp = int(tmp)
						if int(symb2.text) == tmp:
							jump = instrukce_jump(instrukce, root)
							if jump == 1:
								return 1
							else:
								return 0
						else:
							return
					else:
						print("Chyba: Neodpovidaji typy - nemuzeme porovnat", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
					sys.exit(54) # TODO
			elif symb3.attrib['type'] == 'int':
				if int(symb2.text) == int(symb3.text):
					jump = instrukce_jump(instrukce, root)
					if jump == 1:
						return 1
					else:
						return 0
				else:
					return				
			else:
				print("Chyba: Neodpovidaji typy - nemuzeme porovnat", file=sys.stderr)
				sys.exit(53) # TODO
		elif symb2.attrib['type'] == 'bool':
			if symb3.attrib['type'] == 'var':
				if is_declared(symb3.text[3:], symb3_frame) == 0:
					if je_v_promenne_typ(symb3.text[3:], symb3_frame, "bool") == 0:
						tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
						if symb2.text == tmp:
							jump = instrukce_jump(instrukce, root)
							if jump == 1:
								return 1
							else:
								return 0
						else:
							return
					else:
						print("Chyba: Neodpovidaji typy - nemuzeme porovnat", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
					sys.exit(54) # TODO
			elif symb3.attrib['type'] == 'bool':
				if symb2.text == symb3.text:
					jump = instrukce_jump(instrukce, root)
					if jump == 1:
						return 1
					else:
						return 0
				else:
					return
			else:
				print("Chyba: Neodpovidaji typy - nemuzeme porovnat", file=sys.stderr)
				sys.exit(53) # TODO
		else:
			print("Chyba: nemozne", file=sys.stderr)
			sys.exit(53) # TODO
	else:
		print("Chyba: Chcete skocit na neexistujici label", file=sys.stderr)
		sys.exit(52) # TODO
def instrukce_jumpifneq(instrukce, root):
	label = instrukce.find("arg1")
	symb2 = instrukce.find("arg2")
	symb3 = instrukce.find("arg3")

	if label.attrib['type'] != 'label':
		print("Chyba: spatny typ", file=sys.stderr)
		sys.exit(53) # TODO

	if symb2.attrib['type'] == "var":
		if symb2.text[:3] == "GF@":
			symb2_frame = "GF"
		elif symb2.text[:3] == "LF@":
			symb2_frame = "LF"
		elif symb2.text[:3] == "TF@":
			symb2_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
			sys.exit(40) # TODO

	if symb3.attrib['type'] == "var":
		if symb3.text[:3] == "GF@":
			symb3_frame = "GF"
		elif symb3.text[:3] == "LF@":
			symb3_frame = "LF"
		elif symb3.text[:3] == "TF@":
			symb3_frame = "TF"
			if temp_frame_defined == 0:
				print("Chyba: temp_frame_defined je nula a chceme s tim enco delat", file=sys.stderr)
				sys.exit(55) # TODO
		else:
			print("Chyba: Tady by se to nikdy dostat nemelo", file=sys.stderr)
			sys.exit(40) # TODO	

	# nejprve zkontrolujeme, zda existuje label, na ktery chceme skocit
	if label_exist(label.text) == 0:
		# pokud je prvni symbol promenna
		# musime zjistit, co se v promenne nachazi za typ
		if symb2.attrib['type'] == 'var':
			if is_declared(symb2.text[3:], symb2_frame) == 0:
				# TODO - musime zkontrolovat, jestli pormenna existuje
				# pokud je i druhy symbol promenna
				# musime zase zjistit, co se v promenne nachazi za typ
				if symb3.attrib['type'] == 'var':
					if is_declared(symb3.text[3:], symb3_frame) == 0:
						# pokud se typ symbolu1 a symbolu2 nerovnaji, musi skoncit chybou
						typ1 = vrat_typ_promenne(symb2.text[3:], symb2_frame)
						typ2 = vrat_typ_promenne(symb3.text[3:], symb3_frame)
						if typ1 != typ2:
							print("Chyba: neodpovidaji typy", file=sys.stderr)
							sys.exit(53) # TODO
						else:
							tmp1 = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame) 
							tmp2 = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
							# pokud jsou typu int
							if je_v_promenne_typ(symb2.text[3:], symb2_frame, "int") == 0:
								if int(tmp2) != int(tmp1):
									jump = instrukce_jump(instrukce, root)
									if jump == 1:
										return 1
									else:
										return 0
								else:
									return
							# pro zbytek to muzeme udelat najednou
							else:
								if tmp2 != tmp1:
									jump = instrukce_jump(instrukce, root)
									if jump == 1:
										return 1
									else:
										return 0
								else:
									return							
					else:
						print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
						sys.exit(54) # TODO

				# pokud je druhy symbol integet
				elif symb3.attrib['type'] == 'int':
					# musime porovnat, jestli jsou oba symboly stejneho typu
					typ1 = vrat_typ_promenne(symb2.text[3:], symb2_frame)
					if typ1 != 'int':
						print("Chyba: Neodpovidaji typy - nemuzeme porovnat", file=sys.stderr)
						sys.exit(53) # TODO
					tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame)
					tmp = int(tmp)
					if int(symb3.text) != tmp:
						jump = instrukce_jump(instrukce, root)
						if jump == 1:
							return 1
						else:
							return 0
					else:
						return
				# pokud je druhy symbol typu bool
				elif symb3.attrib['type'] == 'bool':
					# musime porovnat, jestli jsou oba symboly stejneho typu
					typ1 = vrat_typ_promenne(symb2.text[3:], symb2_frame)
					if typ1 != 'bool':
						print("Chyba: Neodpovidaji typy - nemuzeme porovnat", file=sys.stderr)
						sys.exit(53) # TODO
					tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame)
					if symb3.text != tmp:
						jump = instrukce_jump(instrukce, root)
						if jump == 1:
							return 1
						else:
							return 0
					else:
						return
				# pokud je druhy symbol typu string
				elif symb3.attrib['type'] == 'string':
					# musime porovnat, jestli jsou oba symboly stejneho typu
					typ1 = vrat_typ_promenne(symb2.text[3:], symb2_frame)
					if typ1 != 'string':
						print("Chyba: Neodpovidaji typy - nemuzeme porovnat", file=sys.stderr)
						sys.exit(53) # TODO
					tmp = vrat_hodnotu_promenne(symb2.text[3:], symb2_frame)
					if symb3.text != tmp:
						jump = instrukce_jump(instrukce, root)
						if jump == 1:
							return 1
						else:
							return 0
					else:
						return
				else:
					print("Chyba: nemozne", file=sys.stderr)
					sys.exit(53) # TODO
			else:
				print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
				sys.exit(54) # TODO
		elif symb2.attrib['type'] == 'string':
			if symb3.attrib['type'] == 'var':
				if is_declared(symb3.text[3:], symb3_frame) == 0:
					# musi byt string
					if je_v_promenne_typ(symb3.text[3:], symb3_frame, "string") == 0:
						tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame)
						if symb2.text != tmp:
							jump = instrukce_jump(instrukce, root)
							if jump == 1:
								return 1
							else:
								return 0
						else:
							return
					else:
						print("Chyba: Neodpovidaji typy - nemuzeme porovnat", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
					sys.exit(54) # TODO
			elif symb3.attrib['type'] == 'string':
				if symb2.text != symb3.text:
					jump = instrukce_jump(instrukce, root)
					if jump == 1:
						return 1
					else:
						return 0
				else:
					return
			else:
				print("Chyba: Neodpovidaji typy - nemuzeme porovnat", file=sys.stderr)
				sys.exit(53) # TODO
		elif symb2.attrib['type'] == 'int':
			if symb3.attrib['type'] == 'var':
				if is_declared(symb3.text[3:], symb3_frame) == 0:
					if je_v_promenne_typ(symb3.text[3:], symb3_frame, "int") == 0:
						tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame)
						tmp = int(tmp)
						if int(symb2.text) != tmp:
							jump = instrukce_jump(instrukce, root)
							if jump == 1:
								return 1
							else:
								return 0
						else:
							return
					else:
						print("Chyba: Neodpovidaji typy - nemuzeme porovnat", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
					sys.exit(54) # TODO
			elif symb3.attrib['type'] == 'int':
				if int(symb2.text) != int(symb3.text):
					jump = instrukce_jump(instrukce, root)
					if jump == 1:
						return 1
					else:
						return 0
				else:
					return				
			else:
				print("Chyba: Neodpovidaji typy - nemuzeme porovnat", file=sys.stderr)
				sys.exit(53) # TODO
		elif symb2.attrib['type'] == 'bool':
			if symb3.attrib['type'] == 'var':
				if is_declared(symb3.text[3:], symb3_frame) == 0:
					if je_v_promenne_typ(symb3.text[3:], symb3_frame, "bool") == 0:
						tmp = vrat_hodnotu_promenne(symb3.text[3:], symb3_frame) 
						if symb2.text != tmp:
							jump = instrukce_jump(instrukce, root)
							if jump == 1:
								return 1
							else:
								return 0
						else:
							return
					else:
						print("Chyba: Neodpovidaji typy - nemuzeme porovnat", file=sys.stderr)
						sys.exit(53) # TODO
				else:
					print("Chyba: Promenna nebyla deklarovana", file=sys.stderr)
					sys.exit(54) # TODO
			elif symb3.attrib['type'] == 'bool':
				if symb2.text != symb3.text:
					jump = instrukce_jump(instrukce, root)
					if jump == 1:
						return 1
					else:
						return 0
				else:
					return
			else:
				print("Chyba: Neodpovidaji typy - nemuzeme porovnat", file=sys.stderr)
				sys.exit(53) # TODO
		else:
			print("Chyba: nemozne", file=sys.stderr)
			sys.exit(53) # TODO
	else:
		print("Chyba: Chcete skocit na neexistujici label", file=sys.stderr)
		sys.exit(52) # TODO

# TODO kontrola, jestli funguje jak ma
def instrukce_drpint(instrukce):
	for child in instrukce:
		if child.attrib['type'] == 'string':
			print(child.text, file=sys.stderr)
		elif child.attrib['type'] == 'int':
			print(child.text, file=sys.stderr)
		elif child.attrib['type'] == 'bool':
			print(child.text, file=sys.stderr)
		elif child.attrib['type'] == 'var':
			# mame proste vypsat obsah, takze asi nezalezi na typu
			# ale musi se kontrolovat, jestli promenna existuje
			if is_declared(child.text[3:],2) == 0:
				tmp = vrat_hodnotu_promenne(child.text[3:], child.text[:2]) 
				print(tmp, file=sys.stderr)
			else:
				print("Chyba: Promenna nebyla dekalrovana", file=sys.stderr)
				sys.exit(53) # TODO		
		else:
			print("Chyba: Nemuze nastat", file=sys.stderr)
			sys.exit(53) # TODO		

# TODO - ma byt na standartni chybovy vystup
def instrukce_break(instrukce):
	print("*******************************************", file=sys.stderr)
	print("            GLOBALNI RAMEC:", file=sys.stderr)
	print(global_frame)
	print("-------------------------------------------", file=sys.stderr)
	print("      GLOBALNI RAMEC - datovy typ", file=sys.stderr)
	print(global_frame_types)
	print("-------------------------------------------", file=sys.stderr)
	print("            LOKALNI RAMEC:", file=sys.stderr)
	print(local_frame)
	print("-------------------------------------------", file=sys.stderr)
	print("      LOKALNI RAMEC - datovy typ", file=sys.stderr)
	print(local_frame_types)
	print("-------------------------------------------", file=sys.stderr)
	print("            DOCASNY RAMEC:", file=sys.stderr)
	print(temp_frame)
	print("-------------------------------------------", file=sys.stderr)
	print("            DOCASNY RAMEC - datovy typ:", file=sys.stderr)
	print(temp_frame_types)
	print("-------------------------------------------", file=sys.stderr)
	print("         ZASOBNIK LOKALNICH RAMCU:", file=sys.stderr)
	print(zasobnik_lokalnich_ramcu)
	print("-------------------------------------------", file=sys.stderr)
	print("      ZASOBNIK LOKALNICH RAMCU - datovy typ:", file=sys.stderr)
	print(zasobnik_lokalnich_ramcu_typ)
	print("-------------------------------------------", file=sys.stderr)
	print("            SEZNAM LABELU:", file=sys.stderr)
	print(label_list)
	print("-------------------------------------------", file=sys.stderr)
	print("            ZASOBNIK VOLANI:", file=sys.stderr)
	print(zasobnik_volani)
	print("*******************************************", file=sys.stderr)







# funkce, ktea overi, zda je instrukce ve spravnem foramtu
# INSTRUKCE promenna
def check_var(instruction, kod):
	# pocet argumentu u techto funcki musi byt roven 1
	if len(instruction) != 1:
		print("Chyba: Ve funkci check_var - neodpovida pocet argumentu", file=sys.stderr)
		sys.exit(32)
	if instruction[0].tag != "arg1":
		print("Chyba: Ve funkci check_var - tag musi byt <arg1>", file=sys.stderr)
		sys.exit(32)
	for child in instruction:
		variable = is_var(child) # jedna se o promennou?
		if tmp_local == 1:
			i = 1 # pracujeme s lokalnim ramcem
		elif tmp_global == 1:
			i = 2 # pracujeme s globalnim ramcem
		elif tmp_temp == 1:
			i = 3 # pracujeme s docasnym ramcem
		else:
			print("Chyba: Tady bych se nikdy nemel dostat - chyba v pomocnych ramcich", file=sys.stderr)
			sys.exit(39) # TODO

		# TODO - muzu deklarovat znovu jiz deklarovanou promennou?
		# TODO - zatim funguje pouze pro DEFVAR, potom budu muset rozlisovat o jakou instrukci pujde

		# promenna, jeste nebyla deklarovana
		if is_declared(variable, i) == 1:
			if tmp_local == 1:
				local_frame[variable] = ""
			elif tmp_global == 1:
				global_frame[variable] = ""
			elif tmp_temp == 1:
				temp_frame[variable] = ""
		# promenna jiz byla deklarovana
		else:
			print("Chyba: Snazite se deklarovat promennou, ktera jiz byla deklarovana", file=sys.stderr)
			sys.exit(30) # TODO navratovy kod
# funkce, ktera zkontroluje, zda instrukce je ve formatu INSTRUKCE promenna symbol
# TODO - myslim, ze ji muzem celou smazat
def check_var_symb(instruction, kod):
	# promenne, ktere slouzi k tomu, abychom v ramci jedne instrukce dokazali rict, jestli pracujeme se stejnymi ramci
	# proste musime vedet s kterymi ramci pracujeme
	var_frame_type = 0
	symb_frame_type = 0
	if len(instruction) != 2:
		print("Chyba: Ve funkci check_var_symb - neodpovida pocet argumentu", file=sys.stderr)
		sys.exit(32)
	# zkontrolujeme, jestli jsou tagy u argumentu odlisne
	if instruction[0].tag == instruction[1].tag:
		print("Chyba: Ve funkci check_var_symb - arguemnty maji stejne cislo", file=sys.stderr)
		sys.exit(32)
	# projdeme jednotlive argumenty a kontrolujeme, jestli se nachazi prave jeden arg1 a jeden arg2
	# argumenty nemusi byt ve spravnem poradi
	for child in instruction:
		# nejedna se o arg1
		if child.tag != 'arg1':
			# musi to tedy byt arg2, pokud ne, tak chyba
			if child.tag != 'arg2':
				print("Chyba: Ve funkci check_var_symb - tagy", file=sys.stderr)
				sys.exit(32)
			# druhy argument musi byt symbol
			else:
				symbol = is_symb(child)
				if tmp_var == 1:
					symbol = is_var(child)
					if tmp_local == 1:
						symb_frame_type = 1
						if is_declared(symbol, 1) == 0:
							symbol = local_frame[symbol] # musime ziskat hodnotu z promenne
						else:
							print("Chyba: Promenna neexistuje a chceme k ni pristoupit", file=sys.stderr)
							sys.exit(54) # TODO tohl by melo byt za behu
					elif tmp_global == 1:
						symb_frame_type = 2
						if is_declared(symbol, 2) == 0:
							symbol = global_frame[symbol] # musime ziskat hodnotu z promenne
						else:
							print("Chyba: Promenna neexistuje a chceme k ni pristoupit", file=sys.stderr)
							sys.exit(54) # TODO
					elif tmp_temp == 1:
						symb_frame_type = 3
						if is_declared(symbol, 3) == 0:
							symbol = temp_frame[symbol] # musime ziskat hodnotu z promenne
						else:
							print("Chyba: Promenna neexistuje a chceme k ni pristoupit", file=sys.stderr)
							sys.exit(54) # TODO
					else:
						print("Chyba: Nemuzu se sem nikdy dostat - jinak nastala chyba v ramcich", file=sys.stderr)
						sys.exit(39) # TODO

				# TODO - musime mit indikatory toho, jestli se jedna o promennou, sting, bool nebo int
				# TODO zatim to mam jen pro string - automaticky je vr string

		# prvni argument musi byt promenna
		else:
			variable = is_var(child) # jedna se o promennou?
			if tmp_local == 1:
				i = 1 # pracujeme s lokalnim ramcem
				var_frame_type = 1
			elif tmp_global == 1:
				i = 2 # pracujeme s globalnim ramcem
				var_frame_type = 2
			elif tmp_temp == 1:
				i = 3 # pracujeme s docasnym ramcem
				var_frame_type = 3
			else:
				print("Chyba: Tady bych se nikdy nemel dostat - chyba v pomocnych ramcich", file=sys.stderr)
				sys.exit(39) # TODO
			# u vsech instrukci tohoto typu musi byt promenna jiz deklarovana
			if is_declared(variable, i) == 1:
				print("Chyba: Promenna nebyla deklarovana a snazime se k ni pristoupit", file=sys.stderr)
				sys.exit(54)

	# pokud se jedna o instrukci MOVE
	if kod == 11:
		if var_frame_type == 1:
			local_frame[variable] = symbol # provedeme operaci MOVE nad lokalnim ramcem
		elif var_frame_type == 2:
			global_frame[variable] = symbol # provedeme operaci MOVE nad globalnim ramcem
		elif var_frame_type == 3:
			temp_frame[variable] = symbol # provedeme operaci MOVE nad docasnym ramcem
		else:
			print("Chyba", file=sys.stderr)
			sys.exit(39) # TODO
# funkce, ktera zkontroluje, jestli se jedna o promennou
# pokud se jedna o promennou, vraci jmeno promenne
def is_var(var):
	# nejprve musime vynulovat pomocne promenne
	globals()['tmp_local'] = 0
	globals()['tmp_global'] = 0
	globals()['tmp_temp'] = 0
	globals()['tmp_string'] = 0
	globals()['tmp_int'] = 0
	globals()['tmp_bool'] = 0
	globals()['tmp_var'] = 0	
	# pocet atributu nesmi byt jiny nez 1
	if len(var.attrib) != 1:
		print("Chyba: is_var - pocet atributu", file=sys.stderr)
		sys.exit(32)
	# projdeme vsechny atributy - v tomto pripade jen jediny
	#pokud jediny atribut neni 'type' -> chyba
	for key in var.attrib:
		if key != 'type':
			print("Chyba: is_var - neobsahuje atribut 'type'", file=sys.stderr)
			sys.exit(32)
	# pokud typ argumentu neni promenna -> nejedna se o promennou -> chyba
	if var.attrib['type'] != 'var':
		print("Chyba: Nejedna se o promennou", file=sys.stderr)
		sys.exit(32)
	# vytahneme z textu elemetnu typ ramce a nazev promenne
	if(re.match('(G|T|L)F@\w+', var.text)):
		promenna = var.text[3:] # ulozime si promennou
		if var.text[:3] == "LF@":
			globals()['tmp_local'] = 1
		elif var.text[:3] == "GF@":
			globals()['tmp_global'] = 1
		elif var.text[:3] == "TF@":
			globals()['tmp_temp'] = 1
		else:
			print("Chyba: Spatny format promenne", file=sys.stderr)
			sys.exit(52) # TODO	
	else:
		print("Chyba: Spatny format promenne", file=sys.stderr)
		sys.exit(52) # TODO
	return promenna;
# funkce, ktera zkontroluje, jestli se jedna o symbol
# u promenne - vraci nazev
# string - vraci string
# bool - true/false
# int - vraci cislo
def is_symb(symb):
	# nejdrive musime vynulovat pomocne promenne
	globals()['tmp_local'] = 0
	globals()['tmp_global'] = 0
	globals()['tmp_temp'] = 0
	globals()['tmp_string'] = 0
	globals()['tmp_int'] = 0
	globals()['tmp_bool'] = 0
	globals()['tmp_var'] = 0	
	# pokud je pocet atributu jiny nez 1
	if len(symb.attrib) != 1:
		print("Chyba: is_symb - pocet atributu", file=sys.stderr)
		sys.exit(32)
	# projdeme vschny atributy - v tomto pripade pouze jeden
	for key in symb.attrib:
		if key != 'type':
			print("Chyba: is_symb - neobsahuje atribut 'type'", file=sys.stderr)
			sys.exit(32)
	# musime zjistit o jaky ty se jedna - nastavime globani prepinace a ulozime si hodnoty
	# TODO - pokud bude typ int, je potreba overit, ze bude i obsah integer - stejne u ostatnich
	if symb.attrib['type'] == 'var':
		text = is_var(symb)
		globals()['tmp_var'] = 1
	elif symb.attrib['type'] == 'string':
		text = symb.text
		globals()['tmp_string'] = 1
	elif symb.attrib['type'] == 'bool':
		text = symb.text
		globals()['tmp_bool'] = 1
	elif symb.attrib['type'] == 'int':
		text = symb.text
		globals()['tmp_int'] = 1
	return text
# funkce, ktera vynuluje vsechny docasne promenne
def vynuluj():
	globals()['tmp_local'] = 0
	globals()['tmp_global'] = 0
	globals()['tmp_temp'] = 0
	globals()['tmp_string'] = 0
	globals()['tmp_int'] = 0
	globals()['tmp_bool'] = 0
	globals()['tmp_var'] = 0


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#
#		MAIN FUNCTION
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
def main():
	global tree # XML musi byt globalni, abychom s nim mohli pracovat v ruznych funkcich

	# pomocne promenne - abychom si pamatovali s kterym ramcem pracujeme
	global tmp_local
	tmp_local = 0
	global tmp_global
	tmp_global = 0
	global tmp_temp
	tmp_temp = 0

	# pomocne promenne, abycom vedel, s cim pracujeme
	global tmp_string
	global tmp_int
	global tmp_bool
	global tmp_var
	tmp_string = 0
	tmp_int = 0
	tmp_bool = 0
	tmp_var = 0

	# ramce - slovniky
	global local_frame
	global local_frame_types
	global global_frame
	global global_frame_types
	global temp_frame
	global temp_frame_types
	global temp_frame_defined
	globals()['temp_frame_defined'] = 0
	local_frame = {}
	local_frame_types = {}
	global_frame = {}
	global_frame_types = {}
	temp_frame = {} 
	temp_frame_types = {}
	

	# DO:
	# promenna = var
	# ramec_promenne = GF / LF / TF
	# Z:
	# hodnota = 16515 / sdfsf / true / var
	# ramec = GF/LF/TF/ None
	# typ_hodnoty = string/bool/int/None - nevime
	# pridat_do_promenne("var5", "TF", "sdfsfsdf", None, "string")

	global label_list
	label_list = {}

	global zasobnik_volani
	zasobnik_volani = []

	global datovy_zasobnik
	datovy_zasobnik = []
	global datovy_zasobnik_typ
	datovy_zasobnik_typ = []

	args = check_arguments() # TODO - argumenty jsou uz spravne? + rozsireni

	try:
		tree = etree.parse(args.source[0])
	except:
		sys.exit(31)


	global zasobnik_lokalnich_ramcu
	global zasobnik_lokalnich_ramcu_typ
	zasobnik_lokalnich_ramcu = []
	zasobnik_lokalnich_ramcu_typ = []
	analyza()



if __name__ == "__main__":
    main()