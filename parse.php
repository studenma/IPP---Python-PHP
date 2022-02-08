<?php
	/*
	*
	* Autor: Martin Studeny
	* Projekt: IPP - parser
	* Login: xstude23
	*
	*/
	// TODO - nastaveni merlina - kodovani UTF8, nastaveni locale
	// prikaz: export LC ALL=cs CZ.UTF-8 + nastaveni puTTY

	// globalni promenna - v pripade rozsireni jde o nazev souboru, do ktereho se maji vypisovat statitskty
	$stats;
	$pocet_komentaru = 0;
	$pocet_instrukci = 0;
	$druhy_komentar = 0; // na jednom radku
	$loc_prvni = 0;
	$bez_statistiky = 0;
	$file_name;

	$writer = new XMLWriter();
	$instruction_counter = 1;
	$prvni_prochazeni = 1;

	// prepinace, ktere ukazuji, jestli se jedna o TF GF nebo LF
	$global_T = 0;
	$global_G = 0;
	$global_L = 0;

	// prepinace, ktere ukazuji, jestli se jedna o int, bool nebo string
	$global_int = 0;
	$global_bool = 0;
	$global_string = 0;

	// prepinac, jestli se jedna o true nebo false
	$global_true = 0;
	$global_false = 0;

	/*
	*	pro funkce, ktere vraceji string - pokud dojde k chybe v takove funkci, prepne se tento prepinac na jednicku
	*/
	$global_err_sym_automat = 0;

	// counter, ktery pocita na kterem znaku zrovna jsme
	$cnt = 0;

	// error_reporting(E_ERROR | E_PARSE);

	// define
	define("KONEC", 19); // konec autoamtu
	define("SPATNEJ_KONEC", 20); // konec autoamtu s chybou
	define("DEFVAR", 50);
	define("MOVE", 51);
	define("AND_",52);
	define("ADD",53);
	define("BREAK_",54);
	define("CALL",55);
	define("CONCAT",56);
	define("CREATEFRAME",57);
	define("DPRINT",58);
	define("EQ",59);
	define("GETCHAR",60);
	define("GT",61);
	define("IDIV",62);
	define("INT2CHAR",63);
	define("JUMP",64);
	define("JUMPIFEQ",65);
	define("JUMPIFNEQ",66);
	define("LABEL",67);
	define("LT",68);
	define("MUL",69);
	define("NOT",70);
	define("OR_",71);
	define("POPFRAME",72);
	define("POPS",73);
	define("PUSHFRAME",74);
	define("PUSHS",75);
	define("READ",76);
	define("RETURN_",77);
	define("SETCHAR",78);
	define("STRI2INT",79);
	define("STRLEN",80);
	define("SUB",81);
	define("TYPE",82);
	define("WRITE",83);

	// funkce, ktera vypisuje napovedu
	function print_help() {
		print("NAPOVEDA:\nSkript nacte ze standartniho vstupu zdrojovy kod v IPPcode18, zkontroluje lexikalni a syntaktickou spravnost kodu a vypise na standartni vystup XML reprezentaci programu dle specifikace\n  Skript je mozne spustit s temito argumenty (na poradi nezalezi):\n\t--help\n\t   po vypsani skript konci, nesmi byt zadan s jinymi argumenty\n\t--stats=file\n\t   kde file je soubor, do ktereho se maji vypisovat statistiky\n\t--comments\n\t   vypise do statistik pocet radku, na kterych se vyskytoval komentar\n\t--loc\n\t   vypise do statistik pocet radku s instrukcemi\n");
	} // funkce


	// funkce, ktera kontroluje, jestli byly argumenty zadany spravne
	function check_arguments($argc, $argv) {
		$short_opt = "";
		$long_opt = array(
			"help",
			"stats:",
			"loc", // musi byt zadan i --stats, jinak return 10
			"comments" // musi byt zadan i --stats, jinak return 10
		);
		$arguments = getopt($short_opt, $long_opt);

		// pokud byl zadan neexistujici argument
		if(sizeof($arguments)+1 != $argc) {
			return 1;
		}
		if(isset($arguments["help"])) {
			if($argc == 2) {
				print_help();
				exit(0);
			}
			else {
				// argument --help nemuze byt pouzit s dalsimi argumenty
				return 1; // TODO - exit nesmi byt ve funkcich, ktera ma vracet nejakou navratovou hodnotu 
			}
		}
		// pokud je zadan parametr --loc, ale nebyl zadan parametr --stats
		if(isset($arguments["loc"])) {
			if(!isset($arguments["stats"])) {
				return 1;
			}
		}
		// pokud byl zadan parametr --comments, ale nebyl zadan parametr --stats
		if(isset($arguments["comments"])) {
			if(!isset($arguments["stats"])) {
				return 1;
			}
		}
		if(isset($arguments["stats"])) {
			$GLOBALS["file_name"] = $arguments["stats"];
			if(!isset($arguments["comments"]) || !isset($arguments["loc"])) {
				// nebudeme vypisovat statistiku
				$GLOBALS["bez_statistiky"] = 1;
			}
			if(strcmp($argv[1], "--loc") == 0)
				$GLOBALS["loc_prvni"] = 1;
			else if(strcmp($argv[1], "--comments") == 0)
				$GLOBALS["loc_prvni"] = 0;
			else if(strcmp($argv[2], "--loc") == 0)
				$GLOBALS["loc_prvni"] = 1;
			else if(strcmp($argv[2], "--comments") == 0)
				$GLOBALS["loc_prvni"] = 0;
			else if(strcmp($argv[3], "--loc") == 0)
				$GLOBALS["loc_prvni"] = 1;
			else if(strcmp($argv[3], "--comments") == 0)
				$GLOBALS["loc_prvni"] = 0;
		}
		else {
			$GLOBALS["bez_statistiky"] = 1;
		}
	} // funkce

	// funkce, ktera hleda ve stringu znaky &,<,>, apod. a meni je na format, ktery je OK pro XML
	// vraci opraveny string
	function change_string($string) {
		$arrr = str_split($string);
		$array_vysledek;
		$i = 0;
		while(1) {
			if($arrr[$i] == '&') {
				$array_vysledek = $array_vysledek."&";
				$array_vysledek = $array_vysledek."a";
				$array_vysledek = $array_vysledek."m";
				$array_vysledek = $array_vysledek."p";
				$array_vysledek = $array_vysledek.";";
			}
			else if($arrr[$i] == '<') {
				$array_vysledek = $array_vysledek."&";
				$array_vysledek = $array_vysledek."l";
				$array_vysledek = $array_vysledek."t";
				$array_vysledek = $array_vysledek.";";
			}
			else if($arrr[$i] == '>') {
				$array_vysledek = $array_vysledek."&";
				$array_vysledek = $array_vysledek."g";
				$array_vysledek = $array_vysledek."t";
				$array_vysledek = $array_vysledek.";";
			}
			else {
				$array_vysledek = $array_vysledek.$arrr[$i];
			}
			$i++;
			if($arrr[$i] == NULL)
				break;
		} // while
		return $array_vysledek;
	} // funcke

	// funkce, ktera tiskne XML pro instrukci DEFVAR
	function add_XML_instruction_DEFVAR($arg, $kod) {
		$arg = change_string($arg);
		$GLOBALS["writer"]->startElement("instruction");
			$GLOBALS["writer"]->writeAttribute("order", $GLOBALS["instruction_counter"]);
			$GLOBALS["writer"]->writeAttribute("opcode", $kod);
			$GLOBALS["writer"]->startElement("arg1");
				$GLOBALS["writer"]->writeAttribute("type", "var");
				$GLOBALS["writer"]->writeRaw($arg);
			$GLOBALS["writer"]->endElement();
		$GLOBALS["writer"]->endElement();
		$GLOBALS["instruction_counter"]++;
		$GLOBALS["pocet_instrukci"]++;
	} // funkce

	// funkce, ktera tiskne XML pro instrukci MOVE
	function add_XML_instruction_MOVE($arg1, $arg2, $type) {
		$arg1 = change_string($arg1);
		$arg2 = change_string($arg2);
		$GLOBALS["writer"]->startElement("instruction");
			$GLOBALS["writer"]->writeAttribute("order", $GLOBALS["instruction_counter"]);
			$GLOBALS["writer"]->writeAttribute("opcode", "MOVE");
			$GLOBALS["writer"]->startElement("arg1");
				$GLOBALS["writer"]->writeAttribute("type", "var");
				$GLOBALS["writer"]->writeRaw($arg1);
			$GLOBALS["writer"]->endElement();
			$GLOBALS["writer"]->startElement("arg2");
				if($type == 1)
					$GLOBALS["writer"]->writeAttribute("type", "int");
				else if($type == 2) 
					$GLOBALS["writer"]->writeAttribute("type", "bool");
				else if($type == 3)
					$GLOBALS["writer"]->writeAttribute("type", "string");
				else if($type == 4)
					$GLOBALS["writer"]->writeAttribute("type", "var");
				else {
				}
				$GLOBALS["writer"]->writeRaw($arg2);
			$GLOBALS["writer"]->endElement();
		$GLOBALS["writer"]->endElement();
		$GLOBALS["instruction_counter"]++;
		$GLOBALS["pocet_instrukci"]++;
	} // funkce

	// funkce, ktera tiskne do XML pro instrukce, ktere maji jako argument pouze LABEL
	function add_XML_instruction_LABEL($arg, $kod) {
		$arg = change_string($arg);
		$GLOBALS["writer"]->startElement("instruction");
			$GLOBALS["writer"]->writeAttribute("order", $GLOBALS["instruction_counter"]);
			$GLOBALS["writer"]->writeAttribute("opcode", $kod);
			$GLOBALS["writer"]->startElement("arg1");
				$GLOBALS["writer"]->writeAttribute("type", "label");
				$GLOBALS["writer"]->writeRaw($arg);
			$GLOBALS["writer"]->endElement();
		$GLOBALS["writer"]->endElement();
		$GLOBALS["instruction_counter"]++;	
		$GLOBALS["pocet_instrukci"]++;	
	} // funkce

	// funkce, ktera tiskne XML pro instrukce, ktere nemaji zadny argument
	function add_XML_instruction_PRAZDNO($kod) {
		$GLOBALS["writer"]->startElement("instruction");
			$GLOBALS["writer"]->writeAttribute("order", $GLOBALS["instruction_counter"]);
			$GLOBALS["writer"]->writeAttribute("opcode", $kod);
		$GLOBALS["writer"]->endElement();
		$GLOBALS["instruction_counter"]++;
		$GLOBALS["pocet_instrukci"]++;
	} // funkce

	// funkce, ktera tiskne XML pro instrukce, ktere jsou ve tvaru INSTRUKCE promenna symbol
	function add_XML_instruction_VAR_SYM($arg1, $arg2, $type, $kod) {
		$arg1 = change_string($arg1);
		$arg2 = change_string($arg2);
		$GLOBALS["writer"]->startElement("instruction");
			$GLOBALS["writer"]->writeAttribute("order", $GLOBALS["instruction_counter"]);
			$GLOBALS["writer"]->writeAttribute("opcode", $kod);
			// argument 1
			$GLOBALS["writer"]->startElement("arg1");
				$GLOBALS["writer"]->writeAttribute("type", "var");
				$GLOBALS["writer"]->writeRaw($arg1);
			$GLOBALS["writer"]->endElement();

			// argument 2 
			$GLOBALS["writer"]->startElement("arg2");
				if($type == 1)
					$GLOBALS["writer"]->writeAttribute("type", "int");
				else if($type == 2) 
					$GLOBALS["writer"]->writeAttribute("type", "bool");
				else if($type == 3)
					$GLOBALS["writer"]->writeAttribute("type", "string");
				else if($type == 4)
					$GLOBALS["writer"]->writeAttribute("type", "var");
				$GLOBALS["writer"]->writeRaw($arg2);
			$GLOBALS["writer"]->endElement();		$GLOBALS["writer"]->endElement();
		$GLOBALS["instruction_counter"]++;	
		$GLOBALS["pocet_instrukci"]++;
	} // funkce

	// funkce, ktera tiskne XML pro instrukce, ktere jsou ve tvaru INSTRUKCE label symbol symbol
	function add_XML_instruction_LABEL_SYM_SYM($arg1, $arg2, $arg3, $type1, $type2, $kod) {
		$arg1 = change_string($arg1);
		$arg2 = change_string($arg2);
		$arg3 = change_string($arg3);
		$GLOBALS["writer"]->startElement("instruction");
			$GLOBALS["writer"]->writeAttribute("order", $GLOBALS["instruction_counter"]);
			$GLOBALS["writer"]->writeAttribute("opcode", $kod);
			// argument 1
			$GLOBALS["writer"]->startElement("arg1");
				$GLOBALS["writer"]->writeAttribute("type", "label");
				$GLOBALS["writer"]->writeRaw($arg1);
			$GLOBALS["writer"]->endElement();
			// argument 2
			$GLOBALS["writer"]->startElement("arg2");
				if($type1 == 1)
					$GLOBALS["writer"]->writeAttribute("type", "int");
				else if($type1 == 2)
					$GLOBALS["writer"]->writeAttribute("type", "bool");
				else if($type1 == 3)
					$GLOBALS["writer"]->writeAttribute("type", "string");
				else if($type1 == 4)
					$GLOBALS["writer"]->writeAttribute("type", "var");
				$GLOBALS["writer"]->writeRaw($arg2);
			$GLOBALS["writer"]->endElement();
			// argument 3
			$GLOBALS["writer"]->startElement("arg3");
				if($type2 == 1)
					$GLOBALS["writer"]->writeAttribute("type", "int");
				else if($type2 == 2)
					$GLOBALS["writer"]->writeAttribute("type", "bool");
				else if($type2 == 3)
					$GLOBALS["writer"]->writeAttribute("type", "string");
				else if($type2 == 4)
					$GLOBALS["writer"]->writeAttribute("type", "var");
				$GLOBALS["writer"]->writeRaw($arg3);
			$GLOBALS["writer"]->endElement();
		$GLOBALS["writer"]->endElement();
		$GLOBALS["instruction_counter"]++;
		$GLOBALS["pocet_instrukci"]++;
	} // funkce

	// funkce, ktera tiskne XML pro instrukce, ktere jsou ve tvaru INSTRUKCE promenna symbol symbol
	function add_XML_instruction_VAR_SYM_SYM($arg1, $arg2, $arg3, $type2, $type3, $kod) {
		$arg1 = change_string($arg1);
		$arg2 = change_string($arg2);
		$arg3 = change_string($arg3);
		$GLOBALS["writer"]->startElement("instruction");
			$GLOBALS["writer"]->writeAttribute("order", $GLOBALS["instruction_counter"]);
			$GLOBALS["writer"]->writeAttribute("opcode", $kod);
			// argument 1
			$GLOBALS["writer"]->startElement("arg1");
				$GLOBALS["writer"]->writeAttribute("type", "var");
				$GLOBALS["writer"]->writeRaw($arg1);
			$GLOBALS["writer"]->endElement();
			// argument 2
			$GLOBALS["writer"]->startElement("arg2");
				if($type2 == 1)
					$GLOBALS["writer"]->writeAttribute("type", "int");
				else if($type2 == 2) 
					$GLOBALS["writer"]->writeAttribute("type", "bool");
				else if($type2 == 3)
					$GLOBALS["writer"]->writeAttribute("type", "string");
				else if($type2 == 4)
					$GLOBALS["writer"]->writeAttribute("type", "var");
				$GLOBALS["writer"]->writeRaw($arg2);
			$GLOBALS["writer"]->endElement();
			// argument 3
			$GLOBALS["writer"]->startElement("arg3");
				if($type3 == 1)
					$GLOBALS["writer"]->writeAttribute("type", "int");
				else if($type3 == 2) 
					$GLOBALS["writer"]->writeAttribute("type", "bool");
				else if($type3 == 3)
					$GLOBALS["writer"]->writeAttribute("type", "string");
				else if($type3 == 4)
					$GLOBALS["writer"]->writeAttribute("type", "var");
				$GLOBALS["writer"]->writeRaw($arg3);
			$GLOBALS["writer"]->endElement();
		$GLOBALS["writer"]->endElement();
		$GLOBALS["instruction_counter"]++;
		$GLOBALS["pocet_instrukci"]++;		
	} // funkce

	// funkce, ktera tiskne XML pro instrukce, ktere jsou ve tvaru INSTRUKCE promenna type
	function add_XML_instruction_VAR_TYPE($arg1, $arg2, $type, $kod) {
		$arg1 = change_string($arg1);
		$arg2 = change_string($arg2);
		$GLOBALS["writer"]->startElement("instruction");
			$GLOBALS["writer"]->writeAttribute("order", $GLOBALS["instruction_counter"]);
			$GLOBALS["writer"]->writeAttribute("opcode", $kod);
			// argument 1
			$GLOBALS["writer"]->startElement("arg1");
				$GLOBALS["writer"]->writeAttribute("type", "var");
				$GLOBALS["writer"]->writeRaw($arg1);
			$GLOBALS["writer"]->endElement();
			// argument 2
			$GLOBALS["writer"]->startElement("arg2");
				$GLOBALS["writer"]->writeAttribute("type", "type");
				$GLOBALS["writer"]->writeRaw($arg2);
			$GLOBALS["writer"]->endElement();
		$GLOBALS["writer"]->endElement();
		$GLOBALS["instruction_counter"]++;
		$GLOBALS["pocet_instrukci"]++;
	} // funkce

	// funkce, ktera tiskne XML pro instrukce, ktere jsou ve tvaru INSTRUKCE symbol
	function add_XML_instruction_SYMB($arg, $type, $kod) {
		$arg = change_string($arg);
		$GLOBALS["writer"]->startElement("instruction");
			$GLOBALS["writer"]->writeAttribute("order", $GLOBALS["instruction_counter"]);
			$GLOBALS["writer"]->writeAttribute("opcode", $kod);
			// argument
			$GLOBALS["writer"]->startElement("arg1");
				if($type == 1)
					$GLOBALS["writer"]->writeAttribute("type", "int");
				else if($type == 2) 
					$GLOBALS["writer"]->writeAttribute("type", "bool");
				else if($type == 3)
					$GLOBALS["writer"]->writeAttribute("type", "string");
				else if($type == 4)
					$GLOBALS["writer"]->writeAttribute("type", "var");
				$GLOBALS["writer"]->writeRaw($arg);
			$GLOBALS["writer"]->endElement();
		$GLOBALS["writer"]->endElement();
		$GLOBALS["instruction_counter"]++;		
		$GLOBALS["pocet_instrukci"]++;
	} // funkce

	// funkce, ktera vytiskne hlavicku XML
	function print_XML() {
		$GLOBALS["writer"]->openURI('php://output');
		$GLOBALS["writer"]->startDocument('1.0', 'UTF-8');
		$GLOBALS["writer"]->setIndent(true);
		$GLOBALS["writer"]->setIndentString(str_repeat(" ", 1));
		$GLOBALS["writer"]->startElement("program");
			$GLOBALS["writer"]->writeAttribute("language", "IPPcode18");
		// neni zakonceny, abych mohl postupne pridavat elementy
		// ukonceni probehne az tesne pred ukoncenim skriptu
	} // funkce

	// funkce, ktera nacte vstup a prochazi jej radek po radku
	function loadInput() {
		$obsah = fopen('php://stdin', 'r');

		// projdeme poprve, abychom overili, ze je kod v poradku a budme ho vypisovat do XML
		// dost neefektivni, ale neprisel jsem na to, jak to pomoci XMLwriter udelat lepe - v pripade chyby se vypisovalo XML az do mista, kde nastala chyba - proto nejdriv musime projit, jestli je kod v poradku a az potom vypisovat
		$line = fgets($obsah);
		// projdeme prvni radek, jestli je v poradku, v druhem pruchodu uz nemusime - nic z nej nevypisujeme
		if(isIPPcode($line) == 1) {
			return 1;
		}
		// projdeme cely vstup radek po radku
		while($line != false) {
			$line = fgets($obsah);
			if(automat($line) == 1) {
				return 1;
			}
		}

		// vratime pointer ve vstupu na zacatek
		rewind($obsah);
		
		print_XML(); // uz muzeme vytisknout hlavicku
		// DRUHY PRUCHOD
		// nastavime prepinac prvni_prochazeni na nulu - jde o druhy pruchod - jedine, co meni je to, ze nyni budeme vypisovat XML - jinak prochazi uplne stejne
		$GLOBALS["prvni_prochazeni"] = 0;
		$line = fgets($obsah);
		while($line != false) {
			$line = fgets($obsah);
			if(automat($line) == 1) {
				return 1;
			}
		}
		fclose($obsah);
		return 0;
	}

	// funkce, ktera projde radek a zjisti, jestli odpovida spravnemu formatu .IPPcode18
	// nezalezi na velikosti pismen
	// stavovy automat - viz dokumentace
	// TODO - mohou byt pred timto radkem mezery?
	function isIPPcode($first_line) {
		$arr = str_split($first_line);
		$state = 0;
		$cnt = 0;
		while(1) {
			switch($state) {
				case 0:
					// konec radku
					if(preg_match("/\n/", $arr[$cnt])) {
						$state = 11;
					}
					// mezery, tabulatory, ... zustavame na tomto stavu
					else if(ctype_space($arr[$cnt]))
						$cnt++;
					else if($arr[$cnt] == '.') {
						$cnt++;
						$state = 1;
					}
					else {
						$state = 11;
					}
					break;
				case 1:
					if($arr[$cnt] == 'I' || $arr[$cnt] == 'i') {
						$cnt++;
						$state = 2;
					}
					else
						$state = 11;
					break;
				case 2:
					if($arr[$cnt] == 'P' || $arr[$cnt] == 'p') {
						$cnt++;
						$state = 3;
					}
					else 
						$state = 11;
					break;
				case 3:
					if($arr[$cnt] == 'P' || $arr[$cnt] == 'p') {
						$cnt++;
						$state = 4;
					}
					else 
						$state = 11;
					break;	
				case 4:
					if($arr[$cnt] == 'C' || $arr[$cnt] == 'c') {
						$cnt++;
						$state = 5;
					}
					else {
						$state = 11;
					}
					break;	
				case 5:
					if($arr[$cnt] == 'O' || $arr[$cnt] == 'o') {
						$cnt++;
						$state = 6;
					}
					else {
						$state = 11;
					}
					break;	
				case 6:
					if($arr[$cnt] == 'D' || $arr[$cnt] == 'd') {
						$cnt++;
						$state = 7;
					}
					else 
						$state = 11;
					break;	
				case 7:
					if($arr[$cnt] == 'E' || $arr[$cnt] == 'e') {
						$cnt++;
						$state = 8;
					}
					else 
						$state = 11;
					break;	
				case 8:
					if($arr[$cnt] == '1') {
						$cnt++;
						$state = 9;
					}
					else 
						$state = 11;
					break;	
				case 9:
					if($arr[$cnt] == '8') {
						$cnt++;
						$state = 10;
					}
					else
						$state = 11;
					break;	
				case 10:
					if(preg_match("/\n/", $arr[$cnt])) {
						$cnt++;
						$state = 12;
					}
					else if($arr[$cnt] == '#') {
						$GLOBALS["pocet_komentaru"]++;
						$state = 12;
					}
					else if($arr[$cnt] == NULL) {
						$state = 12;
					}
					else if(ctype_space($arr[$cnt])) {
						$cnt++;
					}
					else {
						$state = 11;
					}
					break;	
			} // switch
			if($state == 11) {
				return 1;
			}
			else if($state == 12) {
				break;
			}
		} // while
		return 0;
	} // funkce

	// hlavni automat
	// funkce, ktera prochazi prvni cast radku a zjistuje o jakou instrukci se jedna (popripade prazdny radek, komentar)
	// kdyz autoamt zjisti, o jakou instrukci se jedna, zavola dalsi automat, podle toho, co dana instrukce ocekava za argumenty
	function automat($line) {
		$arr = str_split($line);
		$state = 0;
		$GLOBALS["cnt"] = 0;
			while(1) {
				switch($state) {
					case 0;
						if($arr[$GLOBALS["cnt"]] == NULL) {
							$state = KONEC;
						}
						else if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
							$GLOBALS["cnt"]++;
							$state = KONEC;
						}
						else if(ctype_space($arr[$GLOBALS["cnt"]])) {
							$GLOBALS["cnt"]++;
						}
						else if($arr[$GLOBALS["cnt"]] == '#') {
							if($GLOBALS["prvni_prochazeni"] == 0) {
								$GLOBALS["pocet_komentaru"]++;
							}
							$state = KONEC; // komentar - ignorujeme vse na tomto radku
							$GLOBALS["cnt"]++;
						}
						// zjistujeme o jakou instrukci se jedna
						// ADD
						else if($arr[$GLOBALS["cnt"]] == 'A' || $arr[$GLOBALS["cnt"]] == 'a') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'D' || $arr[$GLOBALS["cnt"]] == 'd') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'D' || $arr[$GLOBALS["cnt"]] == 'd') {
									$state = ADD;
									$GLOBALS["cnt"]++;
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							// AND
							else if($arr[$GLOBALS["cnt"]] == 'N' || $arr[$GLOBALS["cnt"]] == 'n') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'D' || $arr[$GLOBALS["cnt"]] == 'd') {
									$GLOBALS["cnt"]++;
									$state = AND_;
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						// BREAK
						else if($arr[$GLOBALS["cnt"]] == 'B' || $arr[$GLOBALS["cnt"]] == 'b') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'R' || $arr[$GLOBALS["cnt"]] == 'r') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'E' || $arr[$GLOBALS["cnt"]] == 'e') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'A' || $arr[$GLOBALS["cnt"]] == 'a') {
										$GLOBALS["cnt"]++;
										if($arr[$GLOBALS["cnt"]] == 'K' || $arr[$GLOBALS["cnt"]] == 'k') {
											// TODO - kontrola, jestli je za tim mezera musi byt primo v automatu BREAK
											$GLOBALS["cnt"]++;
											$state = BREAK_;
										}
										else {
											$state = SPATNEJ_KONEC;
										}
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						// CALL CONCAT CREATEFRAME
						else if($arr[$GLOBALS["cnt"]] == 'C' || $arr[$GLOBALS["cnt"]] == 'c') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'A' || $arr[$GLOBALS["cnt"]] == 'a') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'L' || $arr[$GLOBALS["cnt"]] == 'l') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'L' || $arr[$GLOBALS["cnt"]] == 'l') {
										$GLOBALS["cnt"]++;
										$state = CALL;
										// TODO - bez mezery na konci
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else if($arr[$GLOBALS["cnt"]] == 'O' || $arr[$GLOBALS["cnt"]] == 'o') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'N' || $arr[$GLOBALS["cnt"]] == 'n') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'C' || $arr[$GLOBALS["cnt"]] == 'c') {
										$GLOBALS["cnt"]++;
										if($arr[$GLOBALS["cnt"]] == 'A' || $arr[$GLOBALS["cnt"]] == 'a') {
											$GLOBALS["cnt"]++;
											if($arr[$GLOBALS["cnt"]] == 'T' || $arr[$GLOBALS["cnt"]] == 't') {
												$GLOBALS["cnt"]++;
												$state = CONCAT; // TODO je to bez mezery
											}
											else {
												$state = SPATNEJ_KONEC;
											}
										}
										else {
											$state = SPATNEJ_KONEC;
										}
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else if($arr[$GLOBALS["cnt"]] == 'R' || $arr[$GLOBALS["cnt"]] == 'r') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'E' || $arr[$GLOBALS["cnt"]] == 'e') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'A' || $arr[$GLOBALS["cnt"]] == 'a') {
										$GLOBALS["cnt"]++;
										if($arr[$GLOBALS["cnt"]] == 'T' || $arr[$GLOBALS["cnt"]] == 't') {
											$GLOBALS["cnt"]++;
											if($arr[$GLOBALS["cnt"]] == 'E' || $arr[$GLOBALS["cnt"]] == 'e') {
												$GLOBALS["cnt"]++;
												if($arr[$GLOBALS["cnt"]] == 'F' || $arr[$GLOBALS["cnt"]] == 'f') {
													$GLOBALS["cnt"]++;
													if($arr[$GLOBALS["cnt"]] == 'R' || $arr[$GLOBALS["cnt"]] == 'r') {
														$GLOBALS["cnt"]++;
														if($arr[$GLOBALS["cnt"]] == 'A' || $arr[$GLOBALS["cnt"]] == 'a') {
															$GLOBALS["cnt"]++;
															if($arr[$GLOBALS["cnt"]] == 'M' || $arr[$GLOBALS["cnt"]] == 'm') {
																$GLOBALS["cnt"]++;
																if($arr[$GLOBALS["cnt"]] == 'E' || $arr[$GLOBALS["cnt"]] == 'e') {
																	$GLOBALS["cnt"]++;
																	$state = CREATEFRAME; // TODO je to bez mezery
																}
																else {
																	$state = SPATNEJ_KONEC;
																}
															}
															else {
																$state = SPATNEJ_KONEC;
															}
														}
														else {
															$state = SPATNEJ_KONEC;
														}
													}
													else {
														$state = SPATNEJ_KONEC;
													}
												}
												else {
													$state = SPATNEJ_KONEC;
												}
											}
											else {
												$state = SPATNEJ_KONEC;
											}
										}
										else {
											$state = SPATNEJ_KONEC;
										}
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						// DEFVAR DPRINT
						else if($arr[$GLOBALS["cnt"]] == 'D' || $arr[$GLOBALS["cnt"]] == 'd') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'E' || $arr[$GLOBALS["cnt"]] == 'e') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'F' || $arr[$GLOBALS["cnt"]] == 'f') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'V' || $arr[$GLOBALS["cnt"]] == 'v') {
										$GLOBALS["cnt"]++;
										if($arr[$GLOBALS["cnt"]] == 'A' || $arr[$GLOBALS["cnt"]] == 'a') {
											$GLOBALS["cnt"]++;
											if($arr[$GLOBALS["cnt"]] == 'R' || $arr[$GLOBALS["cnt"]] == 'r') {
												$GLOBALS["cnt"]++;
												$state = DEFVAR; // TODO je to bez mezery
											}
											else {
												$state = SPATNEJ_KONEC;
											}
										}
										else {
											$state = SPATNEJ_KONEC;
										}
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else if($arr[$GLOBALS["cnt"]] == 'P' || $arr[$GLOBALS["cnt"]] == 'p') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'R' || $arr[$GLOBALS["cnt"]] == 'r') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'I' || $arr[$GLOBALS["cnt"]] == 'i') {
										$GLOBALS["cnt"]++;
										if($arr[$GLOBALS["cnt"]] == 'N' || $arr[$GLOBALS["cnt"]] == 'n') {
											$GLOBALS["cnt"]++;
											if($arr[$GLOBALS["cnt"]] == 'T' || $arr[$GLOBALS["cnt"]] == 't') {
												$GLOBALS["cnt"]++;
												$state = DPRINT; // TODO - je to bez mezery
											}
											else {
												$state = SPATNEJ_KONEC;
											}
										}
										else {
											$state = SPATNEJ_KONEC;
										}
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						// EQ
						else if($arr[$GLOBALS["cnt"]] == 'E' || $arr[$GLOBALS["cnt"]] == 'e') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'Q' || $arr[$GLOBALS["cnt"]] == 'q') {
								$GLOBALS["cnt"]++;
								$state = EQ; // TODO - bez mezery
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						// GT GETCHAR
						else if($arr[$GLOBALS["cnt"]] == 'G' || $arr[$GLOBALS["cnt"]] == 'g') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'T' || $arr[$GLOBALS["cnt"]] == 't') {
								$GLOBALS["cnt"]++;
								$state = GT; // TODO bez mezery
							}
							else if($arr[$GLOBALS["cnt"]] == 'E' || $arr[$GLOBALS["cnt"]] == 'e') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'T' || $arr[$GLOBALS["cnt"]] == 't') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'C' || $arr[$GLOBALS["cnt"]] == 'c') {
										$GLOBALS["cnt"]++;
										if($arr[$GLOBALS["cnt"]] == 'H' || $arr[$GLOBALS["cnt"]] == 'h') {
											$GLOBALS["cnt"]++;
											if($arr[$GLOBALS["cnt"]] == 'A' || $arr[$GLOBALS["cnt"]] == 'a') {
												$GLOBALS["cnt"]++;
												if($arr[$GLOBALS["cnt"]] == 'R' || $arr[$GLOBALS["cnt"]] == 'r') {
													$state = GETCHAR;
													$GLOBALS["cnt"]++;
												}
												else {
													$state = SPATNEJ_KONEC;
												}
											}
											else {
												$state = SPATNEJ_KONEC;
											}
										}
										else {
											$state = SPATNEJ_KONEC;
										}
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						// IDIV INT2CHAR
						else if($arr[$GLOBALS["cnt"]] == 'I' || $arr[$GLOBALS["cnt"]] == 'i') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'D' || $arr[$GLOBALS["cnt"]] == 'd') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'I' || $arr[$GLOBALS["cnt"]] == 'i') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'V' || $arr[$GLOBALS["cnt"]] == 'v') {
										$GLOBALS["cnt"]++;
										$state = IDIV; // todo bez mezery
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else if($arr[$GLOBALS["cnt"]] == 'N' || $arr[$GLOBALS["cnt"]] == 'n') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'T' || $arr[$GLOBALS["cnt"]] == 't') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == '2') {
										$GLOBALS["cnt"]++;
										if($arr[$GLOBALS["cnt"]] == 'C' || $arr[$GLOBALS["cnt"]] == 'c') {
											$GLOBALS["cnt"]++;
											if($arr[$GLOBALS["cnt"]] == 'H' || $arr[$GLOBALS["cnt"]] == 'h') {
												$GLOBALS["cnt"]++;
												if($arr[$GLOBALS["cnt"]] == 'A' || $arr[$GLOBALS["cnt"]] == 'a') {
													$GLOBALS["cnt"]++;
													if($arr[$GLOBALS["cnt"]] == 'R' || $arr[$GLOBALS["cnt"]] == 'r') {
														$GLOBALS["cnt"]++;
														$state = INT2CHAR; // TODO bez mezery
													}
													else {
														$state = SPATNEJ_KONEC;
													}
												}
												else {
													$state = SPATNEJ_KONEC;
												}
											}
											else {
												$state = SPATNEJ_KONEC;
											}
										}
										else {
											$state = SPATNEJ_KONEC;
										}
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						// JUMP JUMPIFEQ JUMPIFNEQ
						else if($arr[$GLOBALS["cnt"]] == 'J' || $arr[$GLOBALS["cnt"]] == 'j') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'U' || $arr[$GLOBALS["cnt"]] == 'u') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'M' || $arr[$GLOBALS["cnt"]] == 'm') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'P' || $arr[$GLOBALS["cnt"]] == 'p') {
										$GLOBALS["cnt"]++;
										if($arr[$GLOBALS["cnt"]] == 'I' || $arr[$GLOBALS["cnt"]] == 'i') {
											$GLOBALS["cnt"]++;
											if($arr[$GLOBALS["cnt"]] == 'F' || $arr[$GLOBALS["cnt"]] == 'f') {
												$GLOBALS["cnt"]++;
												if($arr[$GLOBALS["cnt"]] == 'E' || $arr[$GLOBALS["cnt"]] == 'e') {
													$GLOBALS["cnt"]++;
													if($arr[$GLOBALS["cnt"]] == 'Q' || $arr[$GLOBALS["cnt"]] == 'q') {
														$GLOBALS["cnt"]++;
														$state = JUMPIFEQ; // TODO bez mezery
													}
													else {
														$state = SPATNEJ_KONEC;
													}
												}
												else if($arr[$GLOBALS["cnt"]] == 'N' || $arr[$GLOBALS["cnt"]] == 'n') {
													$GLOBALS["cnt"]++;
													if($arr[$GLOBALS["cnt"]] == 'E' || $arr[$GLOBALS["cnt"]] == 'e') {
														$GLOBALS["cnt"]++;
														if($arr[$GLOBALS["cnt"]] == 'Q' || $arr[$GLOBALS["cnt"]] == 'q') {
															$GLOBALS["cnt"]++;
															$state = JUMPIFNEQ; // TODO bez mezery
														}
														else {
															$state = SPATNEJ_KONEC;
														}
													}
													else {
														$state = SPATNEJ_KONEC;
													}
												}
												else {
													$state = SPATNEJ_KONEC;
												}
											}
											else {
												$state = SPATNEJ_KONEC;
											}
										}
										else if(ctype_space($arr[$GLOBALS["cnt"]])) {
											// nesmim to tady inkrementovat, ale nechat, aby to bylo bez mezery
											$state = JUMP; // TODO bez mezery
										}
										else {
											$state = SPATNEJ_KONEC;
										}
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						// LABEL LT
						else if($arr[$GLOBALS["cnt"]] == 'L' || $arr[$GLOBALS["cnt"]] == 'l') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'A' || $arr[$GLOBALS["cnt"]] == 'a') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'B' || $arr[$GLOBALS["cnt"]] == 'b') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'E' || $arr[$GLOBALS["cnt"]] == 'e') {
										$GLOBALS["cnt"]++;
										if($arr[$GLOBALS["cnt"]] == 'L' || $arr[$GLOBALS["cnt"]] == 'l') {
											$GLOBALS["cnt"]++;
											$state = LABEL; // TODO - bez mezery
										}
										else {
											$state = SPATNEJ_KONEC;
										}
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else if($arr[$GLOBALS["cnt"]] == 'T' || $arr[$GLOBALS["cnt"]] == 't') {
								$GLOBALS["cnt"]++;
								$state = LT; // TODO bez mezery
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						// MOVE MUL
						else if($arr[$GLOBALS["cnt"]] == 'M' || $arr[$GLOBALS["cnt"]] == 'm') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'O' || $arr[$GLOBALS["cnt"]] == 'o') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'V' || $arr[$GLOBALS["cnt"]] == 'v') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'E' || $arr[$GLOBALS["cnt"]] == 'e') {
										$GLOBALS["cnt"]++;
										$state = MOVE; // TODO - bez mezery
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else if($arr[$GLOBALS["cnt"]] == 'U' || $arr[$GLOBALS["cnt"]] == 'u') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'L' || $arr[$GLOBALS["cnt"]] == 'l') {
									$GLOBALS["cnt"]++;
									$state = MUL; // TODO bez mezery
								}
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						// NOT
						else if($arr[$GLOBALS["cnt"]] == 'N' || $arr[$GLOBALS["cnt"]] == 'n') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'O' || $arr[$GLOBALS["cnt"]] == 'o') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'T' || $arr[$GLOBALS["cnt"]] == 't') {
									$GLOBALS["cnt"]++;
									$state = NOT; // TODO bez mezery
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						// OR
						else if($arr[$GLOBALS["cnt"]] == 'O' || $arr[$GLOBALS["cnt"]] == 'o') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'R' || $arr[$GLOBALS["cnt"]] == 'r') {
								$GLOBALS["cnt"]++;
								$state = OR_;
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						// POPFRAME POPS PUSHFRAME PUSHS
						else if($arr[$GLOBALS["cnt"]] == 'P' || $arr[$GLOBALS["cnt"]] == 'p') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'O' || $arr[$GLOBALS["cnt"]] == 'o') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'P' || $arr[$GLOBALS["cnt"]] == 'p') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'F' || $arr[$GLOBALS["cnt"]] == 'f') {
										$GLOBALS["cnt"]++;
										if($arr[$GLOBALS["cnt"]] == 'R' || $arr[$GLOBALS["cnt"]] == 'r') {
											$GLOBALS["cnt"]++;
											if($arr[$GLOBALS["cnt"]] == 'A' || $arr[$GLOBALS["cnt"]] == 'a') {
												$GLOBALS["cnt"]++;
												if($arr[$GLOBALS["cnt"]] == 'M' || $arr[$GLOBALS["cnt"]] == 'm') {
													$GLOBALS["cnt"]++;
													if($arr[$GLOBALS["cnt"]] == 'E' || $arr[$GLOBALS["cnt"]] == 'e') {
														$GLOBALS["cnt"]++;
														$state = POPFRAME; // TODO bez mezery
													}
													else {
														$state = SPATNEJ_KONEC;
													}
												}
												else {
													$state = SPATNEJ_KONEC;
												}
											}
											else {
												$state = SPATNEJ_KONEC;
											}
										}
										else {
											$state = SPATNEJ_KONEC;
										}
									}
									else if($arr[$GLOBALS["cnt"]] == 'S' || $arr[$GLOBALS["cnt"]] == 's') {
										$GLOBALS["cnt"]++;
										$state = POPS; // TODO bez mezery
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else if($arr[$GLOBALS["cnt"]] == 'U' || $arr[$GLOBALS["cnt"]] == 'u') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'S' || $arr[$GLOBALS["cnt"]] == 's') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'H' || $arr[$GLOBALS["cnt"]] == 'h') {
										$GLOBALS["cnt"]++;
										if($arr[$GLOBALS["cnt"]] == 'F' || $arr[$GLOBALS["cnt"]] == 'f') {
											$GLOBALS["cnt"]++;
											if($arr[$GLOBALS["cnt"]] == 'R' || $arr[$GLOBALS["cnt"]] == 'r') {
												$GLOBALS["cnt"]++;
												if($arr[$GLOBALS["cnt"]] == 'A' || $arr[$GLOBALS["cnt"]] == 'a') {
													$GLOBALS["cnt"]++;
													if($arr[$GLOBALS["cnt"]] == 'M' || $arr[$GLOBALS["cnt"]] == 'm') {
														$GLOBALS["cnt"]++;
														if($arr[$GLOBALS["cnt"]] == 'E' || $arr[$GLOBALS["cnt"]] == 'e') {
															$GLOBALS["cnt"]++;
															$state = PUSHFRAME; // TODO bez mezery
														}
														else {
															$state = SPATNEJ_KONEC;
														}
													}
													else {
														$state = SPATNEJ_KONEC;
													}
												}
												else {
													$state = SPATNEJ_KONEC;
												}
											}
											else {
												$state = SPATNEJ_KONEC;
											}
										}
										else if($arr[$GLOBALS["cnt"]] == 'S' || $arr[$GLOBALS["cnt"]] == 's') {
											$GLOBALS["cnt"]++;
											$state = PUSHS; // TODO bez mezery
										}
										else {
											$state = SPATNEJ_KONEC;
										}
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						// READ RETURN
						else if($arr[$GLOBALS["cnt"]] == 'R' || $arr[$GLOBALS["cnt"]] == 'r') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'E' || $arr[$GLOBALS["cnt"]] == 'e') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'A' || $arr[$GLOBALS["cnt"]] == 'a') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'D' || $arr[$GLOBALS["cnt"]] == 'd') {
										$GLOBALS["cnt"]++;
										$state = READ; // todo bez mezery
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else if($arr[$GLOBALS["cnt"]] == 'T' || $arr[$GLOBALS["cnt"]] == 't') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'U' || $arr[$GLOBALS["cnt"]] == 'u') {
										$GLOBALS["cnt"]++;
										if($arr[$GLOBALS["cnt"]] == 'R' || $arr[$GLOBALS["cnt"]] == 'r') {
											$GLOBALS["cnt"]++;
											if($arr[$GLOBALS["cnt"]] == 'N' || $arr[$GLOBALS["cnt"]] == 'n') {
												$GLOBALS["cnt"]++;
												$state = RETURN_; // TODO bez mezery
											}
											else {
												$state = SPATNEJ_KONEC;
											}
										}
										else {
											$state = SPATNEJ_KONEC;
										}
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						// SETCHAR STRI2INT STRLEN SUB
						else if($arr[$GLOBALS["cnt"]] == 'S' || $arr[$GLOBALS["cnt"]] == 's') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'E' || $arr[$GLOBALS["cnt"]] == 'e') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'T' || $arr[$GLOBALS["cnt"]] == 't') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'C' || $arr[$GLOBALS["cnt"]] == 'c') {
										$GLOBALS["cnt"]++;
										if($arr[$GLOBALS["cnt"]] == 'H' || $arr[$GLOBALS["cnt"]] == 'h') {
											$GLOBALS["cnt"]++;
											if($arr[$GLOBALS["cnt"]] == 'A' || $arr[$GLOBALS["cnt"]] == 'a') {
												$GLOBALS["cnt"]++;
												if($arr[$GLOBALS["cnt"]] == 'R' || $arr[$GLOBALS["cnt"]] == 'r') {
													$GLOBALS["cnt"]++;
													$state = SETCHAR; // TODO bez mezery
												}
												else {
													$state = SPATNEJ_KONEC;
												}
											}
											else {
												$state = SPATNEJ_KONEC;
											}
										}
										else {
											$state = SPATNEJ_KONEC;
										}
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else if($arr[$GLOBALS["cnt"]] == 'T' || $arr[$GLOBALS["cnt"]] == 't') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'R' || $arr[$GLOBALS["cnt"]] == 'r') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'I' || $arr[$GLOBALS["cnt"]] == 'i') {
										$GLOBALS["cnt"]++;
										if($arr[$GLOBALS["cnt"]] == '2') {
											$GLOBALS["cnt"]++;
											if($arr[$GLOBALS["cnt"]] == 'I' || $arr[$GLOBALS["cnt"]] == 'i') {
												$GLOBALS["cnt"]++;
												if($arr[$GLOBALS["cnt"]] == 'N' || $arr[$GLOBALS["cnt"]] == 'n') {
													$GLOBALS["cnt"]++;
													if($arr[$GLOBALS["cnt"]] == 'T' || $arr[$GLOBALS["cnt"]] == 't') {
														$GLOBALS["cnt"]++;
														$state = STRI2INT; // TODO bez mezery
													}
													else {
														$state = SPATNEJ_KONEC;
													}
												}
												else {
													 $state = SPATNEJ_KONEC;
												}
											}
											else {
												$state = SPATNEJ_KONEC;
											}
										}
										else {
											$state = SPATNEJ_KONEC;
										}
									}
									else if($arr[$GLOBALS["cnt"]] == 'L' || $arr[$GLOBALS["cnt"]] == 'l') {
										$GLOBALS["cnt"]++;
										if($arr[$GLOBALS["cnt"]] == 'E' || $arr[$GLOBALS["cnt"]] == 'e') {
											$GLOBALS["cnt"]++;
											if($arr[$GLOBALS["cnt"]] == 'N' || $arr[$GLOBALS["cnt"]] == 'n') {
												$GLOBALS["cnt"]++;
												$state = STRLEN; // TODO bez mezery
											}
											else {
												$state = SPATNEJ_KONEC;
											}
										}
										else {
											 $state = SPATNEJ_KONEC;
										}
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else if($arr[$GLOBALS["cnt"]] == 'U' || $arr[$GLOBALS["cnt"]] == 'u') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'B' || $arr[$GLOBALS["cnt"]] == 'b') {
									$GLOBALS["cnt"]++;
									$state = SUB; // TODO bez mezery
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						// TYPE
						else if($arr[$GLOBALS["cnt"]] == 'T' || $arr[$GLOBALS["cnt"]] == 't') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'Y' || $arr[$GLOBALS["cnt"]] == 'y') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'P' || $arr[$GLOBALS["cnt"]] == 'p') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'E' || $arr[$GLOBALS["cnt"]] == 'e') {
										$GLOBALS["cnt"]++;
										$state = TYPE; // TODO bez mezery
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						// WRITE
						else if($arr[$GLOBALS["cnt"]] == 'W' || $arr[$GLOBALS["cnt"]] == 'w') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'R' || $arr[$GLOBALS["cnt"]] == 'r') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'I' || $arr[$GLOBALS["cnt"]] == 'i') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'T' || $arr[$GLOBALS["cnt"]] == 't') {
										$GLOBALS["cnt"]++;
										if($arr[$GLOBALS["cnt"]] == 'E' || $arr[$GLOBALS["cnt"]] == 'e') {
											$GLOBALS["cnt"]++;
											$state = WRITE; // TODO bez mezery
										}
										else {
											$state = SPATNEJ_KONEC;
										}
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						else {
							$state = SPATNEJ_KONEC;
						}
						break;
				} // switch
				// konec pro pripad prazdneho radku nebo komentare
				if($state == KONEC) {
					break;
				}
				// konec v pripade, ze se nejedna o zadnou z instrukci, nebo doslo k jine chybe
				else if($state == SPATNEJ_KONEC) {
					return 1;
				}
				// pokud se jedna o instrukci DEFVAR, volame automat, ktery ocekava za instrukci promennou
				else if($state == DEFVAR) {
					if(automat_VARR($line, 1) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci MOVE, volame automat pro instuki MOVE
				else if($state == MOVE) {
					if(automat_MOVE($line) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci ADD, volame automat, ktery ocekava format INSTRUKCE promenna symbol symbol
				else if($state == ADD) {
					if(automat_VAR_SYM_SYM($line, 1) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci AND, volame automat, ktery ocekava format INSTRUKCE promenna symbol symbol
				else if($state == AND_) {
					if(automat_VAR_SYM_SYM($line, 8) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci BREAK, volame automat, ktery za instrukci neceka zadny argument
				else if($state == BREAK_) {
					if(automat_PRAZDNO($line, 4) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci CALL, volame automat, ktery ocekava format INSTRUKCE label
				else if($state == CALL) {
					if(automat_LABEL($line, 2) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci CONCAT, volame automat, ktery ocekava format INSTRUKCE promenna symbol symbol
				else if($state == CONCAT) {
					if(automat_VAR_SYM_SYM($line, 11) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci CREATEFRAME, volame automat, ktery za instrukci neceka zadny argument
				else if($state == CREATEFRAME) {
					if(automat_PRAZDNO($line, 1) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci DPRINT, volame automat, ktery ocekava format INSTRUKCE symbol
				else if($state == DPRINT) {
					if(automat_SYMBB($line, 1) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci EQ, volame automat, ktery ocekava format INSTRUKCE promenna symbol symbol
				else if($state == EQ) {
					if(automat_VAR_SYM_SYM($line, 7) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci GETCHAR, volame automat, ktery ocekava format INSTRUKCE promenna symbol symbol
				else if($state == GETCHAR) {
					if(automat_VAR_SYM_SYM($line, 12) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci GT, volame automat, ktery ocekava format INSTRUKCE promenna symbol symbol
				else if($state == GT) {
					if(automat_VAR_SYM_SYM($line, 6) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci IDIV, volame automat, ktery ocekava format INSTRUKCE promenna symbol symbol
				else if($state == IDIV) {
					if(automat_VAR_SYM_SYM($line,4) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci INT2CHAR, volame automat, ktery ocekava format INSTRUKCE promenna symbol
				else if($state == INT2CHAR) {
					if(automat_VAR_SYM($line, 1) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci JUMP, volame automat, ktery ocekava format INSTRUKCE label
				else if($state == JUMP) {
					if(automat_LABEL($line, 3) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci JUMPIFEQ, volame automat, ktery ocekava format INSTRUKCE label symbol symbol
				else if($state == JUMPIFEQ) {
					if(automat_LABEL_SYM_SYM($line, 1) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci JUMPIFNEQ, volame automat, ktery ocekava format INSTRUKCE label symbol symbol
				else if($state == JUMPIFNEQ) {
					if(automat_LABEL_SYM_SYM($line, 2) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci LABEL, volame automat, ktery ocekava format INSTRUKCE label
				else if($state == LABEL) {
					if(automat_LABEL($line, 1) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci LT, volame automat, ktery ocekava format INSTRUKCE promenna symbol symbol
				else if($state == LT) {
					if(automat_VAR_SYM_SYM($line,5) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci MUL, volame automat, ktery ocekava format INSTRUKCE promenna symbol symbol
				else if($state == MUL) {
					if(automat_VAR_SYM_SYM($line,3) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci NOT, volame automat, ktery ocekava format INSTRUKCE promenna symbol
				else if($state == NOT) {
					if(automat_VAR_SYM($line,4) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci OR, volame automat, ktery ocekava format INSTRUKCE promenna symbol symbol
				else if($state == OR_) {
					if(automat_VAR_SYM_SYM($line, 9) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci POPFRAME, volame automat, ktery za instrukci neceka zadny argument
				else if($state == POPFRAME) {
					if(automat_PRAZDNO($line, 2) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci POPS, volame automat, ktery ocekava format INSTRUKCE promenna
				else if($state == POPS) {
					if(automat_VARR($line, 2) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci PUSHFRAME, volame automat, ktery za instrukci neceka zadny argument
				else if($state == PUSHFRAME) {
					if(automat_PRAZDNO($line, 3) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci PUSHS, volame automat, ktery ocekava format INSTRUKCE symbol
				else if($state == PUSHS) {
					if(automat_SYMBB($line, 3) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci READ, volame automat, ktery ocekava format INSTRUKCE promenna type
				else if($state == READ) {
					if(automat_VAR_TYPE($line, 1) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci RETURN, volame automat, ktery za instrukci neceka zadny argument
				else if($state == RETURN_) {
					if(automat_PRAZDNO($line, 5) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci SETCHAR, volame automat, ktery ocekava format INSTRUKCE promenna symbol symbol
				else if($state == SETCHAR) {
					if(automat_VAR_SYM_SYM($line, 13) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci STRI2INT, volame automat, ktery ocekava format INSTRUKCE promenna symbol symbol
				else if($state == STRI2INT) {
					if(automat_VAR_SYM_SYM($line, 10) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci STRLEN, volame automat, ktery ocekava format INSTRUKCE promenna symbol
				else if($state == STRLEN) {
					if(automat_VAR_SYM($line, 2) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci SUB, volame automat, ktery ocekava format INSTRUKCE promenna symbol symbol
				else if($state == SUB) {
					if(automat_VAR_SYM_SYM($line, 2) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci TYPE, volame automat, ktery ocekava format INSTRUKCE promenna symbol
				else if($state == TYPE) {
					if(automat_VAR_SYM($line,3) == 1) {
						return 1;
					}
					else
						break;
				}
				// pokud se jedna o instrukci WRITE, volame automat, ktery ocekava format INSTRUKCE symbol
				else if($state == WRITE) {
					if(automat_SYMBB($line, 2) == 1) {
						return 1;
					}
					else
						break;
				}
			} // while
		return 0;
	} // funkce


	/*
	*
	*
	*	Stavove automaty, pro jednotlive instrukce - v zavislosti na tom, jake argumenty instrukce ocekava
	*
	*
	*/

	// funkce, ktera se zavola po zjisteni, ze na danem radku je instrukce MOVE 
	// zjistuje, jestli je za MOVE to, co tam ma byt - promenna a symbol
	// automat - viz dokumentace
	function automat_MOVE($line) {
		$arg1;
		$type;
		$arg2;
		$arr = str_split($line);
		$state = 0;
		while(1) {
			switch($state) {
				case 0:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
						$state = SPATNEJ_KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
					}
					else {
						// zavolame funkci (dalsi automat), ktery zjistuje, jestli je promenna ve spravnem formatu
						$slovo = automat_var($arr);
						// pokud ve funkci automat_var doslo k chybe
						if($slovo == 1) {
							return 1;
						}
						if($GLOBALS["global_T"] == 1) {
							$arg1 = "TF@".$slovo;
							$GLOBALS["global_T"] = 0;
						}
						else if($GLOBALS["global_L"] == 1) {
							$arg1 = "LF@".$slovo;
							$GLOBALS["global_L"] = 0;
						}
						else if($GLOBALS["global_G"] == 1) {
							$arg1 = "GF@".$slovo;
							$GLOBALS["global_G"] = 0;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
						$slovo = NULL;
						if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
							$state = SPATNEJ_KONEC;
						}
						else if(ctype_space($arr[$GLOBALS["cnt"]])) {
							$state = 1;
						}
						else if($arr[$GLOBALS["cnt"]] == '#') {
							if($GLOBALS["prvni_prochazeni"] == 0) {
								$GLOBALS["pocet_komentaru"]++;
							}
							$state = SPATNEJ_KONEC; // pokud je na konci komentar, muzeme zbytek odignorovat a ukoncit
						}
					}
					break;
					// resime druhej argument
				case 1:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = SPATNEJ_KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
						}
						$state = SPATNEJ_KONEC;
					}
					else {
						// volame funkci ,ktera zjistuje, jestli je symbol ve spravnem formatu
						$slovo = automat_symb($arr);
						// pokud doslo k chybe v automat_symb
						if($GLOBALS["global_err_sym_automat"] == 1) {
							return 1;
						}
						if($GLOBALS["global_T"] ==  1) {
							$arg2 = "TF@".$slovo;
							$GLOBALS["global_T"] = 0;
							$type = 4;
						}
						else if($GLOBALS["global_L"] == 1) {
							$arg2 = "LF@".$slovo;
							$GLOBALS["global_L"] = 0;
							$type = 4;
						}
						else if($GLOBALS["global_G"] == 1) {
							$arg2 = "GF@".$slovo;
							$GLOBALS["global_G"] = 0;
							$type = 4;
						}
						else if($GLOBALS["global_int"] == 1) {
							$arg2 = $slovo;
							$GLOBALS["global_int"] = 0;
							$type = 1;
						}
						else if($GLOBALS["global_bool"] == 1) {
							$type = 2;
							if($GLOBALS["global_true"] == 1) {
								$arg2 = "true";
								$GLOBALS["global_true"] = 0;
								$GLOBALS["global_bool"] = 0;
							}	
							else if($GLOBALS["global_false"] == 1) {
								$arg2 = "false";
								$GLOBALS["global_false"] = 0;
								$GLOBALS["global_bool"] = 0;
							}	
							else {
								$state = SPATNEJ_KONEC;
							}			
						}
						else if($GLOBALS["global_string"] == 1) {
							$type = 3;
							$arg2 = $slovo;
							$GLOBALS["global_string"] = 0;	
						}
						else {
							$state = SPATNEJ_KONEC;
						}
						$slovo = NULL;
						// tedka budme kontrolovat co se nachazi za symbolem
						if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
							$state = KONEC;
						}
						else if(ctype_space($arr[$GLOBALS["cnt"]])) {
							$state = 2;
						}
						else if($arr[$GLOBALS["cnt"]] == '#') {
							if($GLOBALS["prvni_prochazeni"] == 0) {
								$GLOBALS["pocet_komentaru"]++;
							}
							$state = KONEC; // pokud je na konci komentar, muzeme zbytek odignorovat a ukoncit
						}
						// test na konec souboru
						else if($arr[$GLOBALS["cnt"]] == NULL) {
							$state = KONEC;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
					}
					break;
				case 2:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
						}
						$state = KONEC;
					}
					else if($arr[$GLOBALS["cnt"]] == NULL) {
						$state = KONEC;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
			} // switch
			if($state == KONEC) {
				if($GLOBALS["prvni_prochazeni"] == 0)
					add_XML_instruction_MOVE($arg1, $arg2, $type);
				break;
			}
			else if($state == SPATNEJ_KONEC) {
				return 1;
			}
		} // while
		return 0;
	} // funkce

	// pro instrukce ve formatu INSTRUKCE label symbol symbol
	function automat_LABEL_SYM_SYM($line, $instrukce) {
		$arg1;
		$arg2;
		$arg3;
		$typ1 = 0;
		$typ2 = 0;
		$state = 0;
		$arr = str_split($line);
		while(1) {
			switch($state) {
				// musi prijit mezera
				case 0:
					if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
						$state = 1;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 1:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = SPATNEJ_KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
						}
						$state = SPATNEJ_KONEC;
					}
					else {
						if(preg_match("/\w/", $arr[$GLOBALS["cnt"]])) {
							$slovo = $slovo.$arr[$GLOBALS["cnt"]];
							$GLOBALS["cnt"]++;
							$state = 2;
						}
					}
					break; 
				case 2:
						if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
							$state = SPATNEJ_KONEC;
						}
						else if($arr[$GLOBALS["cnt"]] == '#') {
							if($GLOBALS["prvni_prochazeni"] == 0) {
								$GLOBALS["pocet_komentaru"]++;
							}
							$state = SPATNEJ_KONEC;
						}
						else if($arr[$GLOBALS["cnt"]] == NULL) {
							$state = SPATNEJ_KONEC;
						}
						else if(ctype_space($arr[$GLOBALS["cnt"]])) {
							$state = 3;
							$arg1 = $slovo;
						}
						else if(preg_match("/\w/", $arr[$GLOBALS["cnt"]])) {
							$slovo = $slovo.$arr[$GLOBALS["cnt"]];
							$GLOBALS["cnt"]++;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
						break;
				case 3:
						if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
							$state = SPATNEJ_KONEC;
						}
						else if($arr[$GLOBALS["cnt"]] == '#') {
							if($GLOBALS["prvni_prochazeni"] == 0) {
								$GLOBALS["pocet_komentaru"]++;
							}
							$state = SPATNEJ_KONEC;
						}
						else if($arr[$GLOBALS["cnt"]] == NULL) {
							$state = SPATNEJ_KONEC;
						}
						else if(ctype_space($arr[$GLOBALS["cnt"]])) {
							$GLOBALS["cnt"]++;
						}
						else {
							// SYM 1
							$slovo = automat_symb($arr);
							// pokud doslo k chybe v automat_symb
							if($GLOBALS["global_err_sym_automat"] == 1) {
								return 1;
							}
							if($GLOBALS["global_T"] ==  1) {
								$arg2 = "TF@".$slovo;
								$typ1 = 4;
							}
							else if($GLOBALS["global_L"] == 1) {
								$arg2 = "LF@".$slovo;
								$typ1 = 4;
							}
							else if($GLOBALS["global_G"] == 1) {
								$arg2 = "GF@".$slovo;
								$typ1 = 4;
							}
							else if($GLOBALS["global_int"] == 1) {
								$arg2 = $slovo;
								$typ1 = 1;
							}
							else if($GLOBALS["global_bool"] == 1) {
								$typ1 = 2;
								if($GLOBALS["global_true"] == 1) {
									$arg2 = "true";
								}	
								else if($GLOBALS["global_false"] == 1) {
									$arg2 = "false";
								}	
								else {
									$state = SPATNEJ_KONEC;
								}			
							}
							else if($GLOBALS["global_string"] == 1) {
								$arg2 = $slovo;
								$typ1 = 3;
							}
							else {
								$state = SPATNEJ_KONEC;
							}
							$slovo = NULL;
							// tedka budme kontrolovat co se nachazi za symbolem
							if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
								$state = SPATNEJ_KONEC;
							}
							else if(ctype_space($arr[$GLOBALS["cnt"]])) {
								$state = 4;
							}
							else if($arr[$GLOBALS["cnt"]] == '#') {
								if($GLOBALS["prvni_prochazeni"] == 0) {
									$GLOBALS["pocet_komentaru"]++;
								}
								$state = SPATNEJ_KONEC; // pokud je na konci komentar, muzeme zbytek odignorovat a ukoncit
							}
							else if($arr[$GLOBALS["cnt"]] == NULL) {
								$state = SPATNEJ_KONEC;
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						break;
					case 4:
						if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
							$state = SPATNEJ_KONEC;
						}
						else if($arr[$GLOBALS["cnt"]] == '#') {
							if($GLOBALS["prvni_prochazeni"] == 0) {
								$GLOBALS["pocet_komentaru"]++;
							}
							$state = SPATNEJ_KONEC;
						}
						else if($arr[$GLOBALS["cnt"]] == NULL) {
							$state = SPATNEJ_KONEC;
						}
						else if(ctype_space($arr[$GLOBALS["cnt"]])) {
							$GLOBALS["cnt"]++;
						}
						else {
							// SYM 1
							$slovo = automat_symb($arr);
							// pokud doslo k chybe v automat_symb
							if($GLOBALS["global_err_sym_automat"] == 1) {
								return 1;
							}
							if($GLOBALS["global_T"] ==  1) {
								$arg3 = "TF@".$slovo;
								$typ2 = 4;
							}
							else if($GLOBALS["global_L"] == 1) {
								$arg3 = "LF@".$slovo;
								$typ2 = 4;
							}
							else if($GLOBALS["global_G"] == 1) {
								$arg3 = "GF@".$slovo;
								$typ2 = 4;
							}
							else if($GLOBALS["global_int"] == 1) {
								$arg3 = $slovo;
								$typ2 = 1;
							}
							else if($GLOBALS["global_bool"] == 1) {
								$typ2 = 2;
								if($GLOBALS["global_true"] == 1) {
									$arg3 = "true";
								}	
								else if($GLOBALS["global_false"] == 1) {
									$arg3 = "false";
								}	
								else {
									$state = SPATNEJ_KONEC;
								}			
							}
							else if($GLOBALS["global_string"] == 1) {
								$arg3 = $slovo;
								$typ2 = 3;
							}
							else {
								$state = SPATNEJ_KONEC;
							}
							$slovo = NULL;
							// tedka budme kontrolovat co se nachazi za symbolem
							if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
								$state = KONEC;
							}
							else if(ctype_space($arr[$GLOBALS["cnt"]])) {
								$state = 5;
							}
							else if($arr[$GLOBALS["cnt"]] == '#') {
								if($GLOBALS["prvni_prochazeni"] == 0) {
									$GLOBALS["pocet_komentaru"]++;
								}
								$state = KONEC; // pokud je na konci komentar, muzeme zbytek odignorovat a ukoncit
							}
							else if($arr[$GLOBALS["cnt"]] == NULL) {
								$state = KONEC;
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						break;	
					case 5:
						if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
							$state = KONEC;
						}
						else if(ctype_space($arr[$GLOBALS["cnt"]])) {
							$GLOBALS["cnt"]++;
						}
						else if($arr[$GLOBALS["cnt"]] == '#') {
							if($GLOBALS["prvni_prochazeni"] == 0) {
								$GLOBALS["pocet_komentaru"]++;
							}
							$state = KONEC; // pokud je na konci komentar, muzeme zbytek odignorovat a ukoncit
						}
						else if($arr[$GLOBALS["cnt"]] == NULL) {
							$state = KONEC;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
						break;				
			} // switch
			if($state == KONEC) {
				if($GLOBALS["prvni_prochazeni"] == 0) {
					if($instrukce == 1)
						add_XML_instruction_LABEL_SYM_SYM($arg1, $arg2, $arg3, $typ1, $typ2, "JUMPIFEQ");
					if($instrukce == 2)
						add_XML_instruction_LABEL_SYM_SYM($arg1, $arg2, $arg3, $typ1, $typ2, "JUMPIFNEQ");
				}
				break;
			}
			else if($state == SPATNEJ_KONEC) {
				return 1;
			}			
		} // while
	} // funkce

	// pro instrukce ve formatu INSTRUKCE label
	function automat_LABEL($line, $instrukce) {
		$arg1;
		$state = 0;
		$arr = str_split($line);
		while(1) {
			switch($state) {
				// musi prijit mezera
				case 0:
					if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
						$state = 1;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 1:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = SPATNEJ_KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
						}
						$state = SPATNEJ_KONEC;
					}
					else {
						if(preg_match("/\d/", $arr[$GLOBALS["cnt"]])) {
							$state = SPATNEJ_KONEC;
						}
						else if(preg_match("/\w/", $arr[$GLOBALS["cnt"]])) {
							$slovo = $slovo.$arr[$GLOBALS["cnt"]];
							$GLOBALS["cnt"]++;
							$state = 2;
						}
						else if($arr[$GLOBALS["cnt"]] == '_' || $arr[$GLOBALS["cnt"]] == '-' || $arr[$GLOBALS["cnt"]] == '$' || $arr[$GLOBALS["cnt"]] == '&' || $arr[$GLOBALS["cnt"]] == '%' || $arr[$GLOBALS["cnt"]] == '*') {
							$slovo = $slovo.$arr[$GLOBALS["cnt"]];
							$GLOBALS["cnt"]++;
							$state = 2;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
					}
					break; 
					case 2:
						if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
							$state = KONEC;
						}
						else if($arr[$GLOBALS["cnt"]] == '#') {
							if($GLOBALS["prvni_prochazeni"] == 0) {
								$GLOBALS["pocet_komentaru"]++;
							}
							$state = KONEC;
						}
						else if($arr[$GLOBALS["cnt"]] == NULL) {
							$state = KONEC;
						}
						else if(ctype_space($arr[$GLOBALS["cnt"]])) {
							$state = KONEC;
						}
						else if(preg_match("/\w/", $arr[$GLOBALS["cnt"]])) {
							$slovo = $slovo.$arr[$GLOBALS["cnt"]];
							$GLOBALS["cnt"]++;
						}
						else if($arr[$GLOBALS["cnt"]] == '_' || $arr[$GLOBALS["cnt"]] == '-' || $arr[$GLOBALS["cnt"]] == '$' || $arr[$GLOBALS["cnt"]] == '&' || $arr[$GLOBALS["cnt"]] == '%' || $arr[$GLOBALS["cnt"]] == '*') {
							$slovo = $slovo.$arr[$GLOBALS["cnt"]];
							$GLOBALS["cnt"]++;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
						break;
			} // switch
			if($state == KONEC) {
				if($GLOBALS["prvni_prochazeni"] == 0) {
					if($instrukce == 1) {
						add_XML_instruction_LABEL($slovo, "LABEL");
					}
					else if($instrukce == 2) {
						add_XML_instruction_LABEL($slovo, "CALL");
					}
					else if($instrukce == 3) {
						add_XML_instruction_LABEL($slovo, "JUMP");
					}
				}
				break;
			}
			else if($state == SPATNEJ_KONEC) {
				return 1;
			}
		} // while
	} // funkce

	// pro instrukce, za kterymi se nenachazi zadny argument 
	function automat_PRAZDNO($line, $instrukce) {
		$arr = str_split($line);
		$state = 0;
		while(1) {
			switch($state) {
				// musi prijit mezera
				case 0:
					if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
						$state = 1;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
						}
						$state = KONEC;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 1:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == NULL) {
						$state = KONEC;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
						}
						$state = KONEC;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
			} // swtich
			if($state == KONEC) {
				if($GLOBALS["prvni_prochazeni"] == 0) {
					if($instrukce == 1)
						add_XML_instruction_PRAZDNO("CREATEFRAME");
					else if($instrukce == 2)
						add_XML_instruction_PRAZDNO("POPFRAME");
					else if($instrukce == 3)
						add_XML_instruction_PRAZDNO("PUSHFRAME");
					else if($instrukce == 4)
						add_XML_instruction_PRAZDNO("BREAK");
					else if($instrukce == 5)
						add_XML_instruction_PRAZDNO("RETURN");
				}
				break;
			}
			else if($state == SPATNEJ_KONEC) {
				return 1;
			}
		} // while
	} // funkce

	// pro instrukce ve formatu INSTRUKCE symbol
	function automat_SYMBB($line, $instrukce) {
		$arg1;
		$arr = str_split($line);
		$state = 0;
		$typ;
		while(1) {
			switch($state) {
				// musi prijit mezera
				case 0:
					if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
						$state = 1;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 1:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = SPATNEJ_KONEC;
					}
					else if($arr[$GLOBALS["cnt"]] == NULL) {
						$state = SPATNEJ_KONEC;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
						}
						$state = SPATNEJ_KONEC; // pokud je na konci komentar, muzeme zbytek odignorovat a ukoncit
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
					}
					else {
						$slovo = automat_symb($arr);
						// pokud doslo k chybe v automat_symb
						if($GLOBALS["global_err_sym_automat"] == 1) {
							return 1;
						}
						if($GLOBALS["global_T"] ==  1) {
							$arg1 = "TF@".$slovo;
							$typ = 4;
						}
						else if($GLOBALS["global_L"] == 1) {
							$arg1 = "LF@".$slovo;
							$typ = 4;
						}
						else if($GLOBALS["global_G"] == 1) {
							$arg1 = "GF@".$slovo;
							$typ = 4;
						}
						else if($GLOBALS["global_int"] == 1) {
							$arg1 = $slovo;
							$typ = 1;
						}
						else if($GLOBALS["global_bool"] == 1) {
							$typ = 2;
							if($GLOBALS["global_true"] == 1) {
								$arg1 = "true";
							}	
							else if($GLOBALS["global_false"] == 1) {
								$arg1 = "false";
							}	
							else {
								$state = SPATNEJ_KONEC;
							}			
						}
						else if($GLOBALS["global_string"] == 1) {
							$arg1 = $slovo;
							$typ = 3;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
						$slovo = NULL;
						// tedka budme kontrolovat co se nachazi za symbolem
						if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
							$state = KONEC;
						}
						else if(ctype_space($arr[$GLOBALS["cnt"]])) {
							$state = 2;
						}
						else if($arr[$GLOBALS["cnt"]] == '#') {
							if($GLOBALS["prvni_prochazeni"] == 0) {
								$GLOBALS["pocet_komentaru"]++;
							}
							$state = KONEC; // pokud je na konci komentar, muzeme zbytek odignorovat a ukoncit
						}
						else if($arr[$GLOBALS["cnt"]] == NULL) {
							$state = KONEC;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
						break;
					}
					case 2:
						if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
							$state = KONEC;
						}
						else if($arr[$GLOBALS["cnt"]] == '#') {
							if($GLOBALS["prvni_prochazeni"] == 0) {
								$GLOBALS["pocet_komentaru"]++;
							}
							$state = KONEC; // pokud je na konci komentar, muzeme zbytek odignorovat a ukoncit
						}
						else if(ctype_space($arr[$GLOBALS["cnt"]])) {
							$GLOBALS["cnt"]++;
						}
						else if($arr[$GLOBALS["cnt"]] == NULL) {
							$state = KONEC;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
						break;
			} // switch
			if($state == KONEC) {
				if($GLOBALS["prvni_prochazeni"] == 0) {
					if($instrukce == 1)
						add_XML_instruction_SYMB($arg1, $typ, "DPRINT");
					else if($instrukce == 2)
						add_XML_instruction_SYMB($arg1, $typ, "WRITE");
					else if($instrukce == 3)
						add_XML_instruction_SYMB($arg1, $typ, "PUSHS");
				}
				break;
			}
			else if($state == SPATNEJ_KONEC) {
				return 1;
			}
		} // while
	} // funkce

	// pro instrukce ve formatu INSTRUKCE promenna type
	function automat_VAR_TYPE($line, $instrukce) {
		$arg1;
		$arg2;
		$typ = 0;
		$arr = str_split($line);
		$state = 0;
		while(1) {
			switch($state) {
				// musi prijit mezera
				case 0:
					if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
						$state = 1;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 1:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = SPATNEJ_KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
					}
					else {
						// VAR
						$slovo = automat_var($arr);
						if($slovo == 1) {
							return 1;
						}
						if($GLOBALS["global_T"] ==  1) {
							$arg1 = "TF@".$slovo;
							$GLOBALS["global_T"] = 0;
						}
						else if($GLOBALS["global_L"] == 1) {
							$arg1 = "LF@".$slovo;
							$GLOBALS["global_L"] = 0;
						}
						else if($GLOBALS["global_G"] == 1) {
							$arg1 = "GF@".$slovo;
							$GLOBALS["global_G"] = 0;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
						$slovo = NULL;
						if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
							$state = SPATNEJ_KONEC;
						}
						else if(ctype_space($arr[$GLOBALS["cnt"]])) {
							$state = 2;
						}
						else if($arr[$GLOBALS["cnt"]] == '#') {
							if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
							}
							$state = SPATNEJ_KONEC; // pokud je na konci komentar, muzeme zbytek odignorovat a ukoncit
						}
						else {
							$state = SPATNEJ_KONEC;
						}
					}
					break;
				case 2:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = SPATNEJ_KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
						}
						$state = SPATNEJ_KONEC;
					}
					else if($arr[$GLOBALS["cnt"]] == NULL) {
						$state = SPATNEJ_KONEC;
					}
					else {
						// TYPE
						if($arr[$GLOBALS["cnt"]] == 'i') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'n') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 't') {
									$GLOBALS["cnt"]++;
									$typ = 1;
									$state = 3;
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						else if($arr[$GLOBALS["cnt"]] == 'b') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'o') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'o') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'l') {
										$GLOBALS["cnt"]++;
										$state = 3;
										$typ = 2;
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						else if($arr[$GLOBALS["cnt"]] == 's') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 't') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'r') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'i') {
										$GLOBALS["cnt"]++;
										if($arr[$GLOBALS["cnt"]] == 'n') {
											$GLOBALS["cnt"]++;
											if($arr[$GLOBALS["cnt"]] == 'g') {
												$GLOBALS["cnt"]++;
												$state = 3;
												$typ = 3;
											}
											else {
												$state = SPATNEJ_KONEC;
											}
										}
										else {
											$state = SPATNEJ_KONEC;
										}
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						else {
							$state = SPATNEJ_KONEC;
						}
					}
					break;
				case 3:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$state = 4;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
						}
						$state = KONEC; // pokud je na konci komentar, muzeme zbytek odignorovat a ukoncit
					}
					else if($arr[$GLOBALS["cnt"]] == NULL) {
						$state = KONEC; // pokud je na konci komentar, muzeme zbytek odignorovat a ukoncit
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 4:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
						}
						$state = KONEC; // pokud je na konci komentar, muzeme zbytek odignorovat a ukoncit
					}
					else if($arr[$GLOBALS["cnt"]] == NULL) {
						$state = KONEC; // pokud je na konci komentar, muzeme zbytek odignorovat a ukoncit
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;					
			} // switch
			if($state == KONEC) {
				if($GLOBALS["prvni_prochazeni"] == 0) {
					if($typ == 1)
						$arg2 = "int";
					else if($typ == 2)
						$arg2 = "bool";
					else if($typ == 3)
						$arg2 = "string";
					if($instrukce == 1) {
						add_XML_instruction_VAR_TYPE($arg1, $arg2, $typ, "READ");
					}
				}
				break;
			}
			else if($state == SPATNEJ_KONEC) {
				return 1;
			}	
		} // while
	} // funkce

	// pro instrukce ve formatu INSTRUKCE promenna symbol
	function automat_VAR_SYM($line, $instrukce) {
		$arg1;
		$arg2;
		$typ;
		$arr = str_split($line);
		$state = 0;
		while(1) {
			switch($state) {
				// musi prijit mezera
				case 0:
					if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
						$state = 1;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 1:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = SPATNEJ_KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
					}
					else {
						// VAR
						$slovo = automat_var($arr);
						if($slovo == 1) {
							return 1;
						}
						if($GLOBALS["global_T"] ==  1) {
							$arg1 = "TF@".$slovo;
							$GLOBALS["global_T"] = 0;
						}
						else if($GLOBALS["global_L"] == 1) {
							$arg1 = "LF@".$slovo;
							$GLOBALS["global_L"] = 0;
						}
						else if($GLOBALS["global_G"] == 1) {
							$arg1 = "GF@".$slovo;
							$GLOBALS["global_G"] = 0;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
						$slovo = NULL;
						if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
							$state = SPATNEJ_KONEC;
						}
						else if(ctype_space($arr[$GLOBALS["cnt"]])) {
							$state = 2;
						}
						else if($arr[$GLOBALS["cnt"]] == '#') {
							if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
							}
							$state = SPATNEJ_KONEC; // pokud je na konci komentar, muzeme zbytek odignorovat a ukoncit
						}
						else {
							$state = SPATNEJ_KONEC;
						}
					}
					break;
				case 2:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = SPATNEJ_KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
						}
						$state = SPATNEJ_KONEC;
					}
					else {
						// SYMB
						$slovo = automat_symb($arr);
						// pokud doslo k chybe v automat_symb
						if($GLOBALS["global_err_sym_automat"] == 1) {
							return 1;
						}
						if($GLOBALS["global_T"] ==  1) {
							$arg2 = "TF@".$slovo;
							$typ = 4;
						}
						else if($GLOBALS["global_L"] == 1) {
							$arg2 = "LF@".$slovo;
							$typ = 4;
						}
						else if($GLOBALS["global_G"] == 1) {
							$arg2 = "GF@".$slovo;
							$typ = 4;
						}
						else if($GLOBALS["global_int"] == 1) {
							$arg2 = $slovo;
							$typ = 1;
						}
						else if($GLOBALS["global_bool"] == 1) {
							$typ = 2;
							if($GLOBALS["global_true"] == 1) {
								$arg2 = "true";
							}	
							else if($GLOBALS["global_false"] == 1) {
								$arg2 = "false";
							}	
							else {
								$state = SPATNEJ_KONEC;
							}			
						}
						else if($GLOBALS["global_string"] == 1) {
							$arg2 = $slovo;
							$typ = 3;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
						$slovo = NULL;
						// tedka budme kontrolovat co se nachazi za symbolem
						if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
							$state = KONEC;
						}
						else if(ctype_space($arr[$GLOBALS["cnt"]])) {
							$state = 3;
						}
						else if($arr[$GLOBALS["cnt"]] == '#') {
							if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
							}
							$state = KONEC; // pokud je na konci komentar, muzeme zbytek odignorovat a ukoncit
						}
						else if($arr[$GLOBALS["cnt"]] == NULL) {
							$state = KONEC;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
					}						
					break;
				case 3:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
						}
						$state = KONEC;
					}
					else if($arr[$GLOBALS["cnt"]] == NULL) {
						$state = KONEC;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;					
			} // switch
			if($state == KONEC) {
				if($GLOBALS["prvni_prochazeni"] == 0) {
					if($instrukce == 1)
						add_XML_instruction_VAR_SYM($arg1, $arg2, $typ, "INT2CHAR");
					else if($instrukce == 2)
						add_XML_instruction_VAR_SYM($arg1, $arg2, $typ, "STRLEN");
					else if($instrukce == 3)
						add_XML_instruction_VAR_SYM($arg1, $arg2, $typ, "TYPE");
					else if($instrukce == 4)
						add_XML_instruction_VAR_SYM($arg1, $arg2, $typ, "NOT");
				}
				break;
			}
			else if($state == SPATNEJ_KONEC) {
				return 1;
			}
		} // while
	} // function

	// pro instrukce ve formatu INSTRUKCE promenna symbol symbol
	function automat_VAR_SYM_SYM($line, $instrukce) {
		$arg1;
		$arg2;
		$arg3;
		$typ1; // 1 int 2 bool 3 string
		$typ2;
		$arr = str_split($line);
		$state = 0;
		while(1) {
			switch($state) {
				// musi prijit mezera nebo tab
				case 0:
					if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
						$state = 1;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 1:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = SPATNEJ_KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
					}
					else {
						// VAR
						$slovo = automat_var($arr);
						if($slovo == 1) {
							return 1;
						} 
						if($GLOBALS["global_T"] ==  1) {
							$arg1 = "TF@".$slovo;
							$GLOBALS["global_T"] = 0;
						}
						else if($GLOBALS["global_L"] == 1) {
							$arg1 = "LF@".$slovo;
							$GLOBALS["global_L"] = 0;
						}
						else if($GLOBALS["global_G"] == 1) {
							$arg1 = "GF@".$slovo;
							$GLOBALS["global_G"] = 0;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
						$slovo = NULL;
						if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
							$state = SPATNEJ_KONEC;
						}
						else if(ctype_space($arr[$GLOBALS["cnt"]])) {
							$state = 2;
						}
						else if($arr[$GLOBALS["cnt"]] == '#') {
							if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
							}
							$state = SPATNEJ_KONEC; // pokud je na konci komentar, muzeme zbytek odignorovat a ukoncit
						}
						else {

							$state = SPATNEJ_KONEC;
						}
					}
					break;
				case 2:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = SPATNEJ_KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
						}
						$state = SPATNEJ_KONEC;
					}
					else {
						// SYMB 1
						$slovo = automat_symb($arr);
						// pokud doslo k chybe v automat_symb
						if($GLOBALS["global_err_sym_automat"] == 1) {
							return 1;
						}
						if($GLOBALS["global_T"] ==  1) {
							$arg2 = "TF@".$slovo;
							$typ1 = 4;
						}
						else if($GLOBALS["global_L"] == 1) {
							$arg2 = "LF@".$slovo;
							$typ1 = 4;
						}
						else if($GLOBALS["global_G"] == 1) {
							$arg2 = "GF@".$slovo;
							$typ1 = 4;
						}
						else if($GLOBALS["global_int"] == 1) {
							$arg2 = $slovo;
							$typ1 = 1;
						}
						else if($GLOBALS["global_bool"] == 1) {
							$typ1 = 2;
							if($GLOBALS["global_true"] == 1) {
								$arg2 = "true";
							}	
							else if($GLOBALS["global_false"] == 1) {
								$arg2 = "false";
							}	
							else {
								$state = SPATNEJ_KONEC;
							}			
						}
						else if($GLOBALS["global_string"] == 1) {
							$arg2 = $slovo;
							$typ1 = 3;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
						$slovo = NULL;
						// tedka budme kontrolovat co se nachazi za symbolem
						if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
							$state = SPATNEJ_KONEC;
						}
						else if(ctype_space($arr[$GLOBALS["cnt"]])) {
							$state = 3;
						}
						else if($arr[$GLOBALS["cnt"]] == '#') {
							if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
							}
							$state = SPATNEJ_KONEC; // pokud je na konci komentar, muzeme zbytek odignorovat a ukoncit
						}
						else if($arr[$GLOBALS["cnt"]] == NULL) {
							$state = SPATNEJ_KONEC;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
					}						
					break;
				case 3:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = SPATNEJ_KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
						}
						$state = SPATNEJ_KONEC;
					}
					else if($arr[$GLOBALS["cnt"]] == NULL) {
						$state = SPATNEJ_KONEC;
					}
					else {
						// SYMB 2
						$slovo = automat_symb($arr);
						// pokud doslo k chybe v automat_symb
						if($GLOBALS["global_err_sym_automat"] == 1) {
							return 1;
						}
						if($GLOBALS["global_T"] ==  1) {
							$arg3 = "TF@".$slovo;
							$GLOBALS["global_T"] = 0;
							$typ2 = 4;
						}
						else if($GLOBALS["global_L"] == 1) {
							$arg3 = "LF@".$slovo;
							$GLOBALS["global_L"] = 0;
							$typ2 = 4;
						}
						else if($GLOBALS["global_G"] == 1) {
							$arg3 = "GF@".$slovo;
							$GLOBALS["global_G"] = 0;
							$typ2 = 4;
						}
						else if($GLOBALS["global_int"] == 1) {
							$arg3 = $slovo;
							$typ2 = 1;
						}
						else if($GLOBALS["global_bool"] == 1) {
							$typ2 = 2;
							if($GLOBALS["global_true"] == 1) {
								$arg3 = "true";
							}	
							else if($GLOBALS["global_false"] == 1) {
								$arg3 = "false";
							}	
							else {
								$state = SPATNEJ_KONEC;
							}			
						}
						else if($GLOBALS["global_string"] == 1) {
							$typ2 = 3;
							$arg3 = $slovo;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
						$slovo = NULL;
						// tedka budme kontrolovat co se nachazi za symbolem
						if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
							$state = KONEC;
						}
						else if(ctype_space($arr[$GLOBALS["cnt"]])) {
							$state = 4;
						}
						else if($arr[$GLOBALS["cnt"]] == '#') {
							if($GLOBALS["prvni_prochazeni"] == 0) {
								$GLOBALS["pocet_komentaru"]++;
							}
							$state = KONEC; // pokud je na konci komentar, muzeme zbytek odignorovat a ukoncit
						}
						else if($arr[$GLOBALS["cnt"]] == NULL) {
							$state = KONEC;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
					}						
					break;
				case 4:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
						}
						$state = KONEC;
					}
					else if($arr[$GLOBALS["cnt"]] == NULL) {
						$state = KONEC;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
			} // switch
			if($state == KONEC) {
				if($GLOBALS["prvni_prochazeni"] == 0) {
					if($instrukce == 1)
						add_XML_instruction_VAR_SYM_SYM($arg1, $arg2, $arg3, $typ1, $typ2, "ADD");
					else if($instrukce == 2)
						add_XML_instruction_VAR_SYM_SYM($arg1, $arg2, $arg3, $typ1, $typ2, "SUB");
					else if($instrukce == 3)
						add_XML_instruction_VAR_SYM_SYM($arg1, $arg2, $arg3, $typ1, $typ2, "MUL");
					else if($instrukce == 4)
						add_XML_instruction_VAR_SYM_SYM($arg1, $arg2, $arg3, $typ1, $typ2, "IDIV");
					else if($instrukce == 5)
						add_XML_instruction_VAR_SYM_SYM($arg1, $arg2, $arg3, $typ1, $typ2, "LT");
					else if($instrukce == 6)
						add_XML_instruction_VAR_SYM_SYM($arg1, $arg2, $arg3, $typ1, $typ2, "GT");
					else if($instrukce == 7)
						add_XML_instruction_VAR_SYM_SYM($arg1, $arg2, $arg3, $typ1, $typ2, "EQ");
					else if($instrukce == 8)
						add_XML_instruction_VAR_SYM_SYM($arg1, $arg2, $arg3, $typ1, $typ2, "AND");
					else if($instrukce == 9)
						add_XML_instruction_VAR_SYM_SYM($arg1, $arg2, $arg3, $typ1, $typ2, "OR");
					else if($instrukce == 10)
						add_XML_instruction_VAR_SYM_SYM($arg1, $arg2, $arg3, $typ1, $typ2, "STRI2INT");
					else if($instrukce == 11)
						add_XML_instruction_VAR_SYM_SYM($arg1, $arg2, $arg3, $typ1, $typ2, "CONCAT");
					else if($instrukce == 12)
						add_XML_instruction_VAR_SYM_SYM($arg1, $arg2, $arg3, $typ1, $typ2, "GETCHAR");
					else if($instrukce == 13)
						add_XML_instruction_VAR_SYM_SYM($arg1, $arg2, $arg3, $typ1, $typ2, "SETCHAR");		
				}
				break;
			}
			else if($state == SPATNEJ_KONEC) {
				return 1;
			}
		} // while 
	} // funkce

	// pro instrukce ve formatu INSTRUKCE promenna
	function automat_VARR($line, $instrukce) {
		$arg;
		$arr = str_split($line);
		$state = 6;
		while(1) {
			switch($state) {
				// musi prijit mezera
				case 6:
					if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
						$state = 7;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 7:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = SPATNEJ_KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
					}
					else {
						$slovo = automat_var($arr);
						// pokud doslo ve funkci automat_var k chybe
						if($slovo == 1) {
							return 1;
						}
						if($GLOBALS["global_T"] ==  1) {
							$arg = "TF@".$slovo;
							$GLOBALS["global_T"] = 0;
						}
						else if($GLOBALS["global_L"] == 1) {
							$arg = "LF@".$slovo;
							$GLOBALS["global_L"] = 0;
						}
						else if($GLOBALS["global_G"] == 1) {
							$arg = "GF@".$slovo;
							$GLOBALS["global_G"] = 0;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
						$slovo = NULL;
						if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
							$state = KONEC;
						}
						else if(ctype_space($arr[$GLOBALS["cnt"]])) {
							$state = 8;
						}
						else if($arr[$GLOBALS["cnt"]] == '#') {
							if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
							}
							$state = KONEC; // pokud je na konci komentar, muzeme zbytek odignorovat a ukoncit
						}
						else if($arr[$GLOBALS["cnt"]] == NULL) {
							$state = KONEC;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
					}
					break;
				case 8:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						if($GLOBALS["prvni_prochazeni"] == 0) {
							$GLOBALS["pocet_komentaru"]++;
						}
						$state = KONEC;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
			} // switch
			if($state == KONEC) {
				if($GLOBALS["prvni_prochazeni"] == 0) {
					if($instrukce == 1)
						add_XML_instruction_DEFVAR($arg, "DEFVAR");
					else if($instrukce == 2) 
						add_XML_instruction_DEFVAR($arg, "POPS");
				}
				break;
			}
			else if($state == SPATNEJ_KONEC) {
				return 1;
			}
		} // while
		return 0;
	} // funkce

	// automat, ktery kontroluje spravny format promenne
	// vraci nazev promenne
	function automat_var($arr) {
		$state = 0;
		$GLOBALS["global_T"] = 0;
		$GLOBALS["global_G"] = 0;
		$GLOBALS["global_L"] = 0;
		$slovo = NULL;
		while(1) {
			switch($state) {
				case 0:
					if($arr[$GLOBALS["cnt"]] == 'L') {
						$state = 1;
						$GLOBALS["cnt"]++;
						$GLOBALS["global_L"] = 1;
					}
					else if($arr[$GLOBALS["cnt"]] == 'T') {
						$state = 1;
						$GLOBALS["cnt"]++;
						$GLOBALS["global_T"] = 1;
					}
					else if($arr[$GLOBALS["cnt"]] == 'G') {
						$state = 1;
						$GLOBALS["cnt"]++;
						$GLOBALS["global_G"] = 1;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 1:
					if($arr[$GLOBALS["cnt"]] == 'F') {
						$state = 2;
						$GLOBALS["cnt"]++;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 2:
					if($arr[$GLOBALS["cnt"]] == '@') {
						$state = 3;
						$GLOBALS["cnt"]++;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 3:
					if($arr[$GLOBALS["cnt"]] == '#') {
						$state = SPATNEJ_KONEC;
					}
					else if(preg_match("/\d/", $arr[$GLOBALS["cnt"]])) {
						$state = SPATNEJ_KONEC;
					}
					else if(preg_match("/\w/", $arr[$GLOBALS["cnt"]])) {
						$state = 4;
						$slovo = $slovo.$arr[$GLOBALS["cnt"]];
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == '*' || $arr[$GLOBALS["cnt"]] == '-' || $arr[$GLOBALS["cnt"]] == '_' || $arr[$GLOBALS["cnt"]] == '$' || $arr[$GLOBALS["cnt"]] == '&' || $arr[$GLOBALS["cnt"]] == '%') {
						$state = 4;
						$slovo = $slovo.$arr[$GLOBALS["cnt"]];
						$GLOBALS["cnt"]++;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 4:
					if(preg_match("/\w/", $arr[$GLOBALS["cnt"]])) {
						$slovo = $slovo.$arr[$GLOBALS["cnt"]];
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == '*' || $arr[$GLOBALS["cnt"]] == '-' || $arr[$GLOBALS["cnt"]] == '_' || $arr[$GLOBALS["cnt"]] == '$' || $arr[$GLOBALS["cnt"]] == '&' || $arr[$GLOBALS["cnt"]] == '%') {
						$slovo = $slovo.$arr[$GLOBALS["cnt"]];
						$GLOBALS["cnt"]++;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						return $slovo;
					}
					else if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						return $slovo;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						return $slovo;
					}
					else if($arr[$GLOBALS["cnt"]] == NULL) {
						return $slovo;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
			} // switch
			if($state == SPATNEJ_KONEC) {
				return 1;
			}
		} // while
	} // funkce

	// funkce, ktera kontroluje spravny format
	// \xyz - musi byt cisla
	function automat_cisla($arr) {
		$state = 0;
		$d1;
		$d2;
		$d3;
		while(1) {
			switch($state) {
				case 0:
					if($arr[$GLOBALS["cnt"]] == '\\') {
						$state = 1;
						$GLOBALS["cnt"]++;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 1:
					if(preg_match("/\d/", $arr[$GLOBALS["cnt"]])) {
						$d1 = $arr[$GLOBALS["cnt"]];
						$GLOBALS["cnt"]++;
						if(preg_match("/\d/", $arr[$GLOBALS["cnt"]])) {
							$d2 = $arr[$GLOBALS["cnt"]];
							$GLOBALS["cnt"]++;
							if(preg_match("/\d/", $arr[$GLOBALS["cnt"]])) {
								$d3 = $arr[$GLOBALS["cnt"]];
								$GLOBALS["cnt"]++;
								return "\\".$d1.$d2.$d3;
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						else {
							$state = SPATNEJ_KONEC;
						}
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
			} // switch
			if($state == SPATNEJ_KONEC) {
				return 1;
			}
		} // while
	} // function

	// automat, ktery kontroluje spravny format symbolu
	// vraci nazev symbolu
	// nastavuje prepinace, aby se vedelo, jestli jde o promennou, int, bool, string, LF,TF, GF, apod.
	function automat_symb($arr) {
		$state = 0;
		$cislo;
		$GLOBALS["global_T"] = 0;
		$GLOBALS["global_G"] = 0;
		$GLOBALS["global_L"] = 0;
		$GLOBALS["global_int"] = 0;
		$GLOBALS["global_bool"] = 0;
		$GLOBALS["global_string"] = 0;
		$GLOBALS["global_true"] = 0;
		$GLOBALS["global_false"] = 0;
		$GLOBALS["global_err_sym_automat"] = 0;
		$slovo = NULL;
		while(1) {
			switch($state) {
				case 0:
					if($arr[$GLOBALS["cnt"]] == 'L') {
						$state = 1;
						$GLOBALS["cnt"]++;
						$GLOBALS["global_L"] = 1;
					}
					else if($arr[$GLOBALS["cnt"]] == 'T') {
						$state = 1;
						$GLOBALS["cnt"]++;
						$GLOBALS["global_T"] = 1;
					}
					else if($arr[$GLOBALS["cnt"]] == 'G') {
						$state = 1;
						$GLOBALS["cnt"]++;
						$GLOBALS["global_G"] = 1;
					}
					else if($arr[$GLOBALS["cnt"]] == 'i') {
						$state = 5;
						$GLOBALS["cnt"]++;
						$GLOBALS["global_int"] = 1;
					}
					else if($arr[$GLOBALS["cnt"]] == 'b') {
						$state = 6;
						$GLOBALS["cnt"]++;
						$GLOBALS["global_bool"] = 1;
					}
					else if($arr[$GLOBALS["cnt"]] == 's') {
						$state = 9;
						$GLOBALS["cnt"]++;
						$GLOBALS["global_string"] = 1;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 1:
					// LF / GF / TF
					if($arr[$GLOBALS["cnt"]] == 'F') {
						$state = 2;
						$GLOBALS["cnt"]++;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 2:
					// LF / GF / TF
					if($arr[$GLOBALS["cnt"]] == '@') {
						$state = 3;
						$GLOBALS["cnt"]++;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 3:
				// LF / GF / TF
					if($arr[$GLOBALS["cnt"]] == '#') {
						$state = SPATNEJ_KONEC;
					}
					else if(preg_match("/\d/", $arr[$GLOBALS["cnt"]])) {
						$state = SPATNEJ_KONEC;
					}
					else if(preg_match("/\w/", $arr[$GLOBALS["cnt"]])) {
						$state = 4;
						$slovo = $slovo.$arr[$GLOBALS["cnt"]];
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == '*' || $arr[$GLOBALS["cnt"]] == '-' || $arr[$GLOBALS["cnt"]] == '_' || $arr[$GLOBALS["cnt"]] == '$' || $arr[$GLOBALS["cnt"]] == '&' || $arr[$GLOBALS["cnt"]] == '%') {
						$state = 4;
						$slovo = $slovo.$arr[$GLOBALS["cnt"]];
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == '\\') {
						$cislo = automat_cisla($arr);
						if($cislo == 1) {
							return 1;
						}
						else {
							$slovo = $slovo.$cislo;
							$state = 4;
						}
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 4:
				// LF / GF / TF
					if(preg_match("/\w/", $arr[$GLOBALS["cnt"]])) {
						$slovo = $slovo.$arr[$GLOBALS["cnt"]];
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == '*' || $arr[$GLOBALS["cnt"]] == '-' || $arr[$GLOBALS["cnt"]] == '_' || $arr[$GLOBALS["cnt"]] == '$' || $arr[$GLOBALS["cnt"]] == '&' || $arr[$GLOBALS["cnt"]] == '%') {
						$slovo = $slovo.$arr[$GLOBALS["cnt"]];
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == '\\') {
						$cislo = automat_cisla($arr);
						if($cislo == 1) {
							return 1;
						}
						else {
							$slovo = $slovo.$cislo;
						}
						// TODO - \032 automat
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						return $slovo;
					}
					else if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						return $slovo;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						return $slovo;
					}
					else if($arr[$GLOBALS["cnt"]] == NULL) {
						return $slovo; 
					}
					else {

						$state = SPATNEJ_KONEC;
					}
					break;
				case 5:
				// int
					if($arr[$GLOBALS["cnt"]] == 'n') {
						$GLOBALS["cnt"]++;
						if($arr[$GLOBALS["cnt"]] == 't') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == '@') {
								$GLOBALS["cnt"]++;
								$state = 13;
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						else {
							$state = SPATNEJ_KONEC;
						}
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 6:
				// bool
				if($arr[$GLOBALS["cnt"]] == 'o') {
					$GLOBALS["cnt"]++;
					if($arr[$GLOBALS["cnt"]] == 'o') {
						$GLOBALS["cnt"]++;
						if($arr[$GLOBALS["cnt"]] == 'l') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == '@') {
								$GLOBALS["cnt"]++;
								$state = 7;
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						else {
							$state = SPATNEJ_KONEC;
						}
					}
					else {
						$state = SPATNEJ_KONEC;
					}
				}
				else {
					$state = SPATNEJ_KONEC;
				}
				break;
				case 7:
				// true nebo false
					if($arr[$GLOBALS["cnt"]] == 't') {
						$GLOBALS["cnt"]++;
						if($arr[$GLOBALS["cnt"]] == 'r') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'u') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'e') {
									$GLOBALS["cnt"]++;
									$GLOBALS["global_true"] = 1;
									$state = 8;
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						else {
							$state = SPATNEJ_KONEC;
						}
					}
					else if($arr[$GLOBALS["cnt"]] == 'f') {
						$GLOBALS["cnt"]++;
						if($arr[$GLOBALS["cnt"]] == 'a') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'l') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 's') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'e') {
										$GLOBALS["cnt"]++;
										$GLOBALS["global_false"] = 1;
										$state = 8;
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						else {
							$state = SPATNEJ_KONEC;
						}
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 8:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$state = KONEC;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						return $slovo;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 9:
					if($arr[$GLOBALS["cnt"]] == 't') {
						$GLOBALS["cnt"]++;
						if($arr[$GLOBALS["cnt"]] == 'r') {
							$GLOBALS["cnt"]++;
							if($arr[$GLOBALS["cnt"]] == 'i') {
								$GLOBALS["cnt"]++;
								if($arr[$GLOBALS["cnt"]] == 'n') {
									$GLOBALS["cnt"]++;
									if($arr[$GLOBALS["cnt"]] == 'g') {
										$GLOBALS["cnt"]++;
										if($arr[$GLOBALS["cnt"]] == '@') {
											$state = 10;
											$GLOBALS["cnt"]++;
										}
										else {
											$state = SPATNEJ_KONEC;
										}
									}
									else {
										$state = SPATNEJ_KONEC;
									}
								}
								else {
									$state = SPATNEJ_KONEC;
								}
							}
							else {
								$state = SPATNEJ_KONEC;
							}
						}
						else {
							$state = SPATNEJ_KONEC;
						}
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 10:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$slovo = NULL; // prazdny retezec
						$state = KONEC;
					}
					else if(preg_match("/\w/", $arr[$GLOBALS["cnt"]])) {
						$slovo = $slovo.$arr[$GLOBALS["cnt"]];
						$GLOBALS["cnt"]++;
						$state = 12;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$state = 11;
						$slovo = NULL; // prazdny retezec
					}
					else if($arr[$GLOBALS["cnt"]] == '\\') {
						$cislo = automat_cisla($arr);
						if($cislo == 1) {
							return 1;
						}
						else {
							$slovo = $slovo.$cislo;
							$state = 12;
						}
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						$state = KONEC;
						$slovo = NULL; // prazdny retezec
					}
					else if($arr[$GLOBALS["cnt"]] == NULL) {
						$state = KONEC;
						$slovo = NULL; // prazdny retezec
					}
					else {
						$slovo = $slovo.$arr[$GLOBALS["cnt"]];
						$GLOBALS["cnt"]++;
						$state = 12;
					}
					break;
				case 11:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]--;
						$state = KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						$GLOBALS["cnt"]--;
						$state = KONEC;
					}
					else if($arr[$GLOBALS["cnt"]] == NULL) {
						$GLOBALS["cnt"]--;
						$state = KONEC;
					}
					else {
						$GLOBALS["cnt"]--;
						$state = KONEC;
					}
					break;
				case 12:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$state = 11;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						$state = SPATNEJ_KONEC;
					}
					else if($arr[$GLOBALS["cnt"]] == NULL) {
						$state = KONEC;
					}
					else if(preg_match("/\w/", $arr[$GLOBALS["cnt"]])) {
						$slovo = $slovo.$arr[$GLOBALS["cnt"]];
						$GLOBALS["cnt"]++;
					}
					else if($arr[$GLOBALS["cnt"]] == '\\') {
						$cislo = automat_cisla($arr);
						if($cislo == 1) {
							return 1;
						}
						else {
							$slovo = $slovo.$cislo;
						}
					}
					else {
						$slovo = $slovo.$arr[$GLOBALS["cnt"]];
						$GLOBALS["cnt"]++;
					}
					break;
				case 13:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = SPATNEJ_KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$state = SPATNEJ_KONEC;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						$state = SPATNEJ_KONEC;
					}
					else if($arr[$GLOBALS["cnt"]] == NULL) {
						$state = SPATNEJ_KONEC;
					}
					else if($arr[$GLOBALS["cnt"]] == '+' || $arr[$GLOBALS["cnt"]] == '-') {
						$slovo = $slovo.$arr[$GLOBALS["cnt"]];
						$GLOBALS["cnt"]++;
						if(preg_match("/\w/", $arr[$GLOBALS["cnt"]])) {
							$state = 14;
						}
						else {
							$state = SPATNEJ_KONEC;
						}
					}
					else if(preg_match("/\w/", $arr[$GLOBALS["cnt"]])) {
						$slovo = $slovo.$arr[$GLOBALS["cnt"]];
						$GLOBALS["cnt"]++;
						$state = 14;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
				case 14:
					if(preg_match("/\n/", $arr[$GLOBALS["cnt"]])) {
						$state = KONEC;
					}
					else if(ctype_space($arr[$GLOBALS["cnt"]])) {
						$state = 11;
					}
					else if($arr[$GLOBALS["cnt"]] == '#') {
						$state = KONEC;
					}
					else if($arr[$GLOBALS["cnt"]] == NULL) {
						$state = KONEC;
					}
					else if(preg_match("/\w/", $arr[$GLOBALS["cnt"]])) {
						$slovo = $slovo.$arr[$GLOBALS["cnt"]];
						$GLOBALS["cnt"]++;
					}
					else {
						$state = SPATNEJ_KONEC;
					}
					break;
			} // switch
			if($state == SPATNEJ_KONEC) {
				$GLOBALS["global_err_sym_automat"] = 1;
				return 1;
			}
			else if($state == KONEC) {
				return $slovo;
			}
		} // while
		return 0;
	} // funkce

	/*
	*
	*
	*	MAIN 
	*
	*
	*/
	if(check_arguments($argc, $argv) == 1) {
		// doslo k chybe pri kontrole argumentu
		fwrite(STDERR, "Chyba: Chyba argumentu\n");
		exit(10);		
	}

	if(loadInput() == 1) {
		exit(21);
	}
	else 
		$GLOBALS["writer"]->endElement(); // ukonceni elementu program	

	// zapis do vystupniho souboru pocet komentaru a instrukci
	if($GLOBALS["bez_statistiky"] == 0) {
		$myfile = fopen($GLOBALS["file_name"], "w") or exit(12);
		if($GLOBALS["loc_prvni"] == 0) {
			$txt = $GLOBALS["pocet_komentaru"]."\n";
			$txt2 = $GLOBALS["pocet_instrukci"]."\n";
		}
		else {
			$txt = $GLOBALS["pocet_instrukci"]."\n";
			$txt2 = $GLOBALS["pocet_komentaru"]."\n";
		}
		fwrite($myfile, $txt);
		fwrite($myfile, $txt2);
		fclose($myfile);		
	}
	exit(0);
?>