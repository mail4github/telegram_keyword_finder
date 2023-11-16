<?php
header('Content-type: text/html');
header('Access-Control-Allow-Origin: *');

$python_folder = '/var/www/telegram_bot/bot_python/';

function tep_sanitize_string($string, $max_length = 0, $allow_html = false, $only_standard_chars = false, 
	$replace_non_standard_chars = '<br>', $replace_quotes = true, $remove_quotes = false, $its_unicode = false, $preg_remove = '') 
{
	if ( $only_standard_chars ) {
		for ($i = 0; $i < strlen($string); $i++ ) {
			if ( intval( ord($string[$i]) ) < intval( ord(' ') ) || intval( ord($string[$i]) ) > intval( ord('~') ) )
				$string[$i] = chr(1);
		}
		$string = str_replace(chr(1), $replace_non_standard_chars, $string);
	}
	
	$string = str_replace("\\", '&#92;', $string);
	if ( $replace_quotes ) {
		$string = preg_replace('/"/', '&quot;', $string);
		$string = preg_replace('/\'/', '&#39;', $string);
	}
	if ( $remove_quotes ) {
		$string = preg_replace('/"/', '', $string);
		$string = preg_replace('/\'/', '', $string);
	}
	if ( !empty($preg_remove) )
		$string = preg_replace($preg_remove, '', $string);

	if ( !$allow_html ) {
		$string = str_replace('<', '&lt;', $string);
		$string = str_replace('>', '&gt;', $string);
	}
	if ( $max_length > 0 ) {
		if ( $its_unicode )
			$string = mb_substr($string, 0, $max_length, 'HTML-ENTITIES');
		else
			$string = substr($string, 0, $max_length);
	}
		
	return $string;
}

function generate_answer($success = 1, $message = '', $values = '', $error_code = '')
{
	return '{"success":'.$success.', "message":"'.$message.'", "error_code":"'.$error_code.'", "values":'.json_encode($values).'}';
}


if (!isset($_POST['api_id']) || empty(@$_POST['api_id']) || empty(@$_POST['api_hash']) || empty(@$_POST['phone'])) {
	echo generate_answer(0, 'empty parameter '.isset($_POST['api_id']).', '.empty(@$_POST['api_id']).', '.empty(@$_POST['api_hash']).', '.empty(@$_POST['phone']));
	exit;
}

$_POST['write_messages_on_screen'] = (@$_POST['write_messages_on_screen'] == '1' ? '1' : '0');

$code_file_name = "tmp_".$_POST['phone']."_code.txt";
$waiting_code_file_name = "tmp_wait_".$_POST['phone']."_code.txt";

$command_line = '';
foreach ($_POST as $key => $value) {
	$command_line = $command_line.(empty($command_line) ? '' : ' ')."$key='".tep_sanitize_string($value)."'";
}
$command = escapeshellcmd("python3 ".$python_folder."bot_command_line.py work_folder='$python_folder' code_file_name='$code_file_name' waiting_code_file_name='$waiting_code_file_name' $command_line");

//echo $command; exit;
$output = shell_exec($command);

echo $output;

?>