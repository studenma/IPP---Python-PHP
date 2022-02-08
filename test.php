<?php  

	$html;
	$test_counter = 0;

	$recursive_on = 0;
	$directory_cesta;
	$directory_cesta_neni = 0;
	$parser_cesta;
	$parser_cesta_neni = 0;
	$interpret_cesta;
	$interpret_cesta_neni = 0;

	$pocet_testu = 0;
	$pocet_uspechu = 0;
	$pocet_neuspechu = 0;

	// funkce, ktera vypisuje napovedu
	function print_help() {
		print("Vypisuji napovedu\n");
	} // funkce

	function html_hlavicka($pocet_testu,$uspech,$neuspech) {
		echo("<!DOCTYPE html><html><head><meta charset=\"UTF-8\">
		<style>
			.a {
				background-color: #99ff66;
			}
			.b {
				background-color: #ff9966;
			}
		 </style>
		<body>
		<div class=\"page\">	
		<h1>Vysledky testovani</h1>
		<div class=\"text\">
		<h3>
		Celkove:
		</h3>
		<p>Pocet testu: $pocet_testu</p>
		<p>Pocet uspesnych testu: $uspech</p>
		<p>Pocet neuspesnych testu: $neuspech</p>
		<h3>
		Jednotlive:
		</h3>");
	} 
	function html_pridat_test($nazev,$uspel, $ocekavana, $vracena,$info) {
		$cislo = $GLOBALS["test_counter"];
		if($uspel == 1) {
			$GLOBALS["html"] = $GLOBALS["html"]."
			<h4>
			Cislo $cislo:
			</h4>
			<div class=\"a\">
			<p><b>Nazev testu:</b> $nazev <br>
			<b>Vyhodnoceni:</b>  USPEL<br>
			<b>Ocekavana navratova hodnota:</b>  $ocekavana<br>
			<b>Vracena navratova hodnota:</b>  $vracena<br>
			<b>Info:</b>  $info <br><p></div>
			";			
		}
		else{
			$GLOBALS["html"] = $GLOBALS["html"]."
			<h4>
			Cislo $cislo:
			</h4>
			<div class=\"b\">
				<p><b>Nazev testu:</b> $nazev <br>
				<b>Vyhodnoceni:</b>  NEUSPEL<br>
				<b>Ocekavana navratova hodnota:</b>  $ocekavana<br>
				<b>Vracena navratova hodnota:</b>  $vracena<br>
				<b>Info:</b>  $info <br><p></div>
			";			
		}

	} 
	// funkce, ktera kontroluje, jestli byly argumenty zadany spravne
	function check_arguments($argc, $argv) {
		$short_opt = "";
		$long_opt = array(
			"help", // vypise napovedu
			"directory:", // testy bude hledav v tomt adresari
			"recursive", // testy bude hledat nejen v zadanem zdresari, ale i rekurzivne ve vsech jeho podadresarich
			"parse-script:", // soubor se skriptem parse.php
			"int-script:" // soubor se skriptem interpret.py
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
				return 1;
			}
		}
		// pokud neni zadan argument directory
		if(isset($arguments["directory"])) {
			$GLOBALS["directory_cesta"] = $arguments["directory"];
		}
		else {
			$GLOBALS["directory_cesta_neni"] = 1;
		}
		if(isset($arguments["recursive"])) {
			$GLOBALS["recursive_on"] = 1;
		}
		if(isset($arguments["parse-script"])) {
			$GLOBALS["parser_cesta"] = $arguments["parse-script"];
		}
		else {
			$GLOBALS["parser_cesta_neni"] = 1;
		}
		if(isset($arguments["int-script"])) {
			$GLOBALS["interpret_cesta"] = $arguments["int-script"];
		}
		else {
			$GLOBALS["interpret_cesta_neni"] = 1;
		}
	} // funkce


	if(check_arguments($argc, $argv) == 1) {
		// doslo k chybe pri kontrole argumentu
		fwrite(STDERR, "Chyba: Chyba argumentu\n");
		exit(10);		
	}

	// POKUD NENI ZAPLE REKURZIVNI PROHLEDAVANI
	if($recursive_on == 0) {
		// POKUD JE ZADANA CESTA K DIRECOTRY
		if($directory_cesta_neni == 0) {
			// HLEDANI SOUBORU - src
			$tmp = $directory_cesta."/*.src";
			$soubory_src = array();
			foreach(glob($tmp) as $file) {
				$soubory_src[] = $file;
			}
			// DOMYSLENI SOUBORU - in
			$soubory_in = array();
			foreach($soubory_src as $soubor) {
				$jmeno = preg_replace('/^.*\x2F/', "", $soubor);
				$jmeno = preg_replace('/\..*/', "", $jmeno);
				$jmeno = $jmeno.".in";
				$soubory_in[] = $directory_cesta."/".$jmeno;
			}
			// DOMYSLENI SOUBORU - out
			$soubory_out = array();
			foreach($soubory_src as $soubor) {
				$jmeno = preg_replace('/^.*\x2F/', "", $soubor);
				$jmeno = preg_replace('/\..*/', "", $jmeno);
				$jmeno = $jmeno.".out";
				$soubory_out[] = $directory_cesta."/".$jmeno;
			}	
			// DOMYSLENI SOUBORU - rc
			$soubory_rc = array();
			foreach($soubory_src as $soubor) {
				$jmeno = preg_replace('/^.*\x2F/', "", $soubor);
				$jmeno = preg_replace('/\..*/', "", $jmeno);
				$jmeno = $jmeno.".rc";
				$soubory_rc[] = $directory_cesta."/".$jmeno;
			}		
		}
		// POKUD NENI ZADANA CESTA K DIRECOTRY
		else {
			// HLEDANI SOUBORU - src
			$tmp = "*.src";
			$soubory_src = array();
			foreach(glob($tmp) as $file) {
				$soubory_src[] = $file;
			}
			// DOMYSLENI SOUBORU - in
			$soubory_in = array();
			foreach($soubory_src as $soubor) {
				$jmeno = preg_replace('/^.*\x2F/', "", $soubor);
				$jmeno = preg_replace('/\..*/', "", $jmeno);
				$jmeno = $jmeno.".in";
				$soubory_in[] = $directory_cesta.$jmeno;
			}
			// DOMYSLENI SOUBORU - out
			$soubory_out = array();
			foreach($soubory_src as $soubor) {
				$jmeno = preg_replace('/^.*\x2F/', "", $soubor);
				$jmeno = preg_replace('/\..*/', "", $jmeno);
				$jmeno = $jmeno.".out";
				$soubory_out[] = $directory_cesta.$jmeno;
			}	
			// DOMYSLENI SOUBORU - rc
			$soubory_rc = array();
			foreach($soubory_src as $soubor) {
				$jmeno = preg_replace('/^.*\x2F/', "", $soubor);
				$jmeno = preg_replace('/\..*/', "", $jmeno);
				$jmeno = $jmeno.".rc";
				$soubory_rc[] = $directory_cesta.$jmeno;
				var_dump($soubory_rc);
			}			
		} // else

		// zkontrolujeme, jestli soubory in existuji
		// jinak se vytvori prazdne
		foreach($soubory_in as $in) {
			if(file_exists($in)) {
				// continue
			}
			else {
				touch($in);
			}
		}
		// zkontrolujeme, jestli soubory out existuji
		// jinak se vytvori prazdne
		foreach($soubory_out as $out) {
			if(file_exists($out)) {
				// continue
			}
			else {
				touch($out);
			}
		}
		// zkontrolujeme, jestli soubory rc existuji
		// jinak se vytvori prazdne
		foreach($soubory_rc as $rc) {
			if(file_exists($rc)) {
				// continue
			}
			else {
				$handle = fopen($rc, "w") or die("Unable to open file!");
				$txt = "0";
				fwrite($handle, $txt);
				fclose($myfile);
			}
		}
	} // if($recursive_on == 0)
	else {
		print("neni implementovano");
		exit(10);
	}

	// projdeme postupne vsechny testy
	foreach($soubory_src as $src) {
		$GLOBALS["pocet_testu"] = $GLOBALS["pocet_testu"] + 1;
		$GLOBALS["test_counter"] = $GLOBALS["test_counter"] +1;
		// soubor.rc
		$file = preg_replace('/^.*\x2F/', "", $src);
		$file = preg_replace('/\..*/', "", $file);
		if($directory_cesta_neni == 0) {
	        if(substr($file, -1) == '/') {
	            // vytvorime si docasny soubor - zde bude vystup parseru
	            $temp_file = $file.".tmp";
	            $temp_file = $directory_cesta.$temp_file;
	            // vytvorime si druhy docasny soubor
	            $temp_file2 = $file.".tmp2";
	            $temp_file2 = $directory_cesta.$temp_file2;
	            // zjistime ze souboru.rc ocekavanou navratovou hodnotu
	            $file_rc = $file.".rc";
	            $file_rc = $directory_cesta.$file_rc;
	            // zjistime ze souboru.out jak bude vypadat vystup
	            $file_out = $file.".out";
	            $file_out = $directory_cesta.$file_out;
	            // zjistime ze souboru.in jak bude vypadat pripadny standartni vstup
	            $file_in = $file.".in";
	            $file_in = $directory_cesta.$file_in;
	        }
	        else {
	            // vytvorime si docasny soubor - zde bude vystup parseru
	            $temp_file = $file.".tmp";
	            $temp_file = $directory_cesta."/".$temp_file;
	            // vytvorime si druhy docasny soubor
	            $temp_file2 = $file.".tmp2";
	            $temp_file2 = $directory_cesta."/".$temp_file2;
	            // zjistime ze souboru.rc ocekavanou navratovou hodnotu
	            $file_rc = $file.".rc";
	            $file_rc = $directory_cesta."/".$file_rc;
	            // zjistime ze souboru.out jak bude vypadat vystup
	            $file_out = $file.".out";
	            $file_out = $directory_cesta."/".$file_out;
	            // zjistime ze souboru.in jak bude vypadat pripadny standartni vstup
	            $file_in = $file.".in";
	            $file_in = $directory_cesta."/".$file_in;
	        }
	    }
	    else {
            $temp_file = $file.".tmp";
            $temp_file = $directory_cesta.$temp_file;
            // vytvorime si druhy docasny soubor
            $temp_file2 = $file.".tmp2";
            $temp_file2 = $directory_cesta.$temp_file2;
            // zjistime ze souboru.rc ocekavanou navratovou hodnotu
            $file_rc = $file.".rc";
            $file_rc = $directory_cesta.$file_rc;
            // zjistime ze souboru.out jak bude vypadat vystup
            $file_out = $file.".out";
            $file_out = $directory_cesta.$file_out;
            // zjistime ze souboru.in jak bude vypadat pripadny standartni vstup
            $file_in = $file.".in";
            $file_in = $directory_cesta.$file_in;	    	
	    }
        if($parser_cesta_neni) {
        	$parser_script = "./parse.php";
        }
        else {
        	$parser_script = $GLOBALS["parser_cesta"];
        }
        if($interpret_cesta_neni) {
        	$inter_script = "./interpret.py";
        }
        else {
        	$inter_script = $GLOBALS["interpret_cesta"];
        }

		// TODO - co kdyz bude v souboru nejaka mezera nebo mit jiny format
		$navratovej_kod = file_get_contents($file_rc, true);
		// spustime parser
		$out2 = array();
		if(is_file($parser_script)) {
			exec("php5.6 $parser_script < $src", $out2, $return);
			// pokud je navratova hodnota 0 -> parser prose v poradku
			if($return == 0) {
				$handle = fopen($temp_file, "w") or die("Unable to open file!");
				fwrite($handle, implode("\n",$out2));
				fclose($handle);
				$out = array();
				if(is_file($inter_script)) {

					exec("python3.6 $inter_script --source=$temp_file < $file_in > $temp_file2", $out, $return);
					$vraceno = $return;
					if($navratovej_kod == $return) {
						$out1 = array();
						exec("diff $temp_file2 $file_out",$out1,$return);
						if(empty($out1)) {
		                        // PARSER I INTERPRET JSOU V PORADKU A VYSTUP SE ROVNA
						    	$v_poradku = 1;
						    	$GLOBALS["pocet_uspechu"] = $GLOBALS["pocet_uspechu"]+1;
						    	html_pridat_test($file,$v_poradku, $navratovej_kod,$vraceno,"Parser i interpret maji ocekavany vystup");                           
		        		}
						else {
		                    // NEUSPECH DIFF
							$v_poradku = 0;
							$GLOBALS["pocet_neuspechu"] = $GLOBALS["pocet_neuspechu"]+1;
							html_pridat_test($file,$v_poradku, $navratovej_kod,0,"Chyba diff");  
						}
					}
					else {
						$v_poradku = 0;
						// print($navratovej_kod."\n");
						// print($return."\n");	
		                $GLOBALS["pocet_neuspechu"] = $GLOBALS["pocet_neuspechu"]+1;
		                html_pridat_test($file,$v_poradku, $navratovej_kod,$return,"Navratove kody se neshoduji - chyba v interpretu");	                  		
					}
					unlink($temp_file);
					unlink($temp_file2);
				}
				else {
					print($inter_script." - neni spustitelny soubor\n");
					exit(10);					
				}
			}
			else {
				if($navratovej_kod == $return) {
					// OCEKAVANA CHYBA PARSERU
	                // OK
	                html_pridat_test($file,1, $navratovej_kod,$return,"Ocekavana chyba v parseru");	
					$GLOBALS["pocet_uspechu"] = $GLOBALS["pocet_uspechu"]+1;
	                $v_poradku = 1;
				}
				else {
					// NEOCEKAVANA CHYBA PARSERU
	                // FAIL
	                html_pridat_test($file,0, $navratovej_kod,$return,"Chyba v parseru - navratove kody se neshoduji");
	                $v_poradku = 0;
					$GLOBALS["pocet_neuspechu"] = $GLOBALS["pocet_neuspechu"]+1;
				}                
			}	
		}
		else {
			print($parser_script." - neni spustitelny soubor\n");
			exit(10);
		}
	}
	// tisk html
	html_hlavicka($GLOBALS["pocet_testu"], $GLOBALS["pocet_uspechu"], $GLOBALS["pocet_neuspechu"]);
	echo $GLOBALS["html"];
?>