<?php
/**
 * Telegram groups parser  -  A web interface to the Python parser
 *
 * @package   index.php
 * @author    Pavel Zh <lancerpavel@mail.ru>
*/

$groups_file_path = 'groups.txt';
$keywords_file_path = 'keywords.txt';
$stopwords_file_path = 'stopwords.txt';
$messages_file_path = 'messages.txt';
$log_file_path = 'log.txt';
$maximum_records_to_store = 500;
$credentials_file_path = '../bot_python/credentials.txt';

/**
 * Generate JSON answer
 * @param  int $success, string $message, string $values, string $error_code
 * @return string
*/

function generate_answer($success = 1, $message = '', $values = '', $error_code = '')
{
	return '{"success":'.$success.', "message":"'.$message.'", "error_code":"'.$error_code.'", "values":'.json_encode($values).'}';
}

/**
 * Save event in the log file
 * @param  array $log_info_arr
 * @return int
*/

function add_to_log($log_info_arr)
{
	global $log_file_path;
	global $maximum_records_to_store;

	if (isset($log_info_arr) && !empty($log_info_arr)) {
		$saved_log_arr = json_decode(file_get_contents($log_file_path), true);
		if (empty($saved_log_arr))
			$saved_log_arr = [];

		while (count($saved_log_arr) > $maximum_records_to_store) {
			unset($saved_log_arr[0]);
			$saved_log_arr = array_values($saved_log_arr);
		}

		$saved_log_arr[] = $log_info_arr;
		file_put_contents($log_file_path, json_encode($saved_log_arr));
		return count($saved_log_arr);
	}
	return 0;
}

/**
 * A function which is used in the sorting
 * @param  array $a, $b
 * @return int
*/

function sort_cmp($a, $b) 
{
	if( $a['group_name'] == $b['group_name'] ) {
		return 0;
	}
	return ($a['group_name'] < $b['group_name']) ? -1 : 1;
}

/**
 * Saving array of groups in the $groups_file_path file by a POST request
*/

if (!empty($_POST['groups_json'])) {
	$received_groups_arr = json_decode(base64_decode($_POST['groups_json']), true);
	$saved_groups_arr = json_decode(file_get_contents($groups_file_path), true);
	for ($i = 0; $i < count($received_groups_arr); $i++) {
		$received_groups_arr[$i]['group_status'] = 'i';
		foreach ($saved_groups_arr as $saved_group) {
			if ($received_groups_arr[$i]['group_id'] == $saved_group['group_id']) {
				$received_groups_arr[$i]['group_status'] = $saved_group['group_status'];
				echo $received_groups_arr[$i]['group_id'].' -> '.$received_groups_arr[$i]['group_status']."<br>";
				break;
			}
		}
	}
	file_put_contents($groups_file_path, json_encode($received_groups_arr));
	exit;
}

/**
 * Parse GET requests which have sent in the 'command' parameter
*/

if (!empty($_GET['command'])) {
	switch ($_GET['command']) {
		case 'get_list_of_groups':
			$received_groups_arr = json_decode(file_get_contents($groups_file_path), true);
			for ($i = 0; $i < count($received_groups_arr); $i++) {
				$received_groups_arr[$i]['group_name'] = base64_decode($received_groups_arr[$i]['group_name']);
			}
			usort($received_groups_arr, 'sort_cmp');
			echo generate_answer(1, '', $received_groups_arr);
		break;
		case 'change_group_status':
			$groups_arr = json_decode(file_get_contents($groups_file_path), true);
			for ($i = 0; $i < count($groups_arr); $i++) {
				if ($groups_arr[$i]['group_id'] == $_GET['group_id']) {
					$groups_arr[$i]['group_status'] = $_GET['group_status'];
					add_to_log(['message' => base64_encode('Status of group "'.base64_decode($groups_arr[$i]['group_name']).'" changed to "'.$_GET['group_status'].'"'), 'color' => 'O', 'unixtime' => time()]);
				}
			}
			file_put_contents($groups_file_path, json_encode($groups_arr));
			echo generate_answer(1, '', $groups_arr);
		break;
		case 'get_groups_to_listen':
			$groups_arr = json_decode(file_get_contents($groups_file_path), true);
			$result_arr = [];
			for ($i = 0; $i < count($groups_arr); $i++) {
				if ($groups_arr[$i]['group_status'] == 'l' || $groups_arr[$i]['group_status'] == 'a') {
					$result_arr[] = $groups_arr[$i];//['group_id'];
				}
			}
			echo generate_answer(1, '', $result_arr);
		break;
		case 'get_keywords':
			echo generate_answer(1, '', file_get_contents($keywords_file_path));
		break;
		case 'save_keywords':
			file_put_contents($keywords_file_path, base64_decode($_GET['keywords']));
			echo generate_answer(1);
		break;
		case 'add_found_messages':
			$saved_message_arr = json_decode(file_get_contents($messages_file_path), true);
			if (empty($saved_message_arr))
				$saved_message_arr = [];
			
			while (count($saved_message_arr) > $maximum_records_to_store) {
				unset($saved_message_arr[0]);
				$saved_message_arr = array_values($saved_message_arr);
			}
			
			$arr = json_decode(base64_decode($_POST['messages']), true);
			for ($i = 0; $i < count($arr); $i++) {
				$already_added = false;
				for ($j = 0; $j < count($saved_message_arr); $j++) {
					if ($arr[$i]['message'] == $saved_message_arr[$j]['message']) {
						$already_added = true;
						break;
					}
				}
				if (!$already_added) {
					$saved_message_arr[] = $arr[$i];
				}
			}
			file_put_contents($messages_file_path, json_encode($saved_message_arr));
			echo generate_answer(1);
		break;
		case 'get_messages':
			echo generate_answer(1, '', file_get_contents($messages_file_path));
		break;
		case 'add_log':
			$res = add_to_log(json_decode(base64_decode($_GET['log']), true));
			echo generate_answer(1, "added record number: $res");
		break;
		case 'get_log':
			echo generate_answer(1, '', file_get_contents($log_file_path));
		break;
		
		case 'get_stopwords':
			echo generate_answer(1, '', file_get_contents($stopwords_file_path));
		break;
		case 'save_stopwords':
			file_put_contents($stopwords_file_path, base64_decode($_GET['stopwords']));
			echo generate_answer(1);
		break;
	}
	exit;
}

/**
 * Perform logout
*/

if ($_GET['page'] == 'logout') {
	setcookie('loggedin', '0');
	header('Location: ?page=set');
	exit;
}

/**
 * Perform login by login name and password
*/

if ($_POST['login_submitted'] == '1') {
	$credentials_arr = json_decode(file_get_contents($credentials_file_path), true);
	if (strtolower(trim($_POST['login_name'])) == $credentials_arr['login_name'] && strtolower(trim($_POST['password'])) == $credentials_arr['password']) {
		setcookie('loggedin', '1');
		header('Location: ?page=work');
		exit;
	}
	else {
		$_COOKIE['loggedin'] == '0';
	}
}

/**
 * Redirect to the specified webpage
*/
if ($_COOKIE['loggedin'] == '1') {
	if ( empty($_GET['page']) )
		$_GET['page'] = 'work';
}
else {
	$_GET['page'] = '';
}

?>
<!DOCTYPE html>
<html lang="ru">
	<head>
		<meta charset="utf-8">
		<meta http-equiv="X-UA-Compatible" content="IE=edge">
		<title>Telegram Bot</title>
		<meta http-equiv="content-type" content="text/html;charset=utf-8" />
		<meta name="description" content="">
		<meta name="keywords" content="">
		<meta name="viewport" content="width=device-width, user-scalable=no">
		<link rel="shortcut icon" href="/tmp_images/favicon.png">
		<link href="/javascript/bootstrap/css/bootstrap.min.css" rel="stylesheet">
		
	<style type="text/css">
		h1{border-bottom: 1px solid #000000; margin-bottom: 0em;}
		form .row{margin-top: 2em;}
		.radio{margin-top:0px; margin-bottom:0px; font-size: 90%;}
		.scrolling_list{border: 1px solid #a7a7a7; border-radius: 6px; padding: 8px 0 8px 10px; max-height: 300px; overflow: auto; background-color: #f2f2f2;}
		.scrolling_list_label{margin-top:2em;}
		.stopword_name,
		.keyword_name{width:100%;}
		.stopword_remove,
		.keyword_remove{min-width:2em;}
		.log_ok{color:#017a01;}
		.log_error{color:#d20000;}
		.log_td_time{min-width: 15em; font-size: 60%;}
	</style>
	<script src="/javascript/pycommon.js" type="text/javascript"></script>
	<script src="/javascript/jquery.min.js"></script>
	<script src="/javascript/jquery-ui.min.js"></script>
	<script type="text/javascript">
	</script>
	</head>
	<body style="padding: 0 0 3em 0;">
	<div class="row" style="max-width: 900px; margin: auto;">
		<div class="col-md-3" style="">
			<div style="border-right: 1px solid #000000;">
				<h3>Menu:</h3>
				<p><a href="?page=set">Settings</a></p>
				<p><a href="?page=work">Work</a></p>
				<p><a href="?page=logout">Logout</a></p>
			</div>
		</div>
		<div class="col-md-9">
			<?php if ($_GET['page'] == 'set') 
			{ ?>
				<h1>Settings</h1>
				<label class="scrolling_list_label">Groups:</label>
				<div class="scrolling_list" id="table_groups"></div>

				<div class="row" style="margin-top: 2em; margin-bottom: 0.5em;">
					<label class="scrolling_list_label col-md-4" style="margin: 0.3em 0 0 0;">Keywords:</label>
					<div class="col-md-8 inputGroupContainer">
						<div class="input-group">
							<span class="input-group-addon">New:</span>
							<input type="text" id="new_keyword" value="" class="form-control" placeholder="New Keyword"> 
							<span class="input-group-btn">
								<button class="btn btn-info" onclick="add_keyword($(`#new_keyword`).val(), true)">Add</button>
							</span>
						</div>
					</div>
				</div>
				<div class="scrolling_list" id="div_keywords" style="background-color:#eaf2ea; color:#047504;"></div>

				<div class="row" style="margin-top: 2em; margin-bottom: 0.5em;">
					<label class="scrolling_list_label col-md-4" style="margin: 0.3em 0 0 0;">Stop words:</label>
					<div class="col-md-8 inputGroupContainer">
						<div class="input-group">
							<span class="input-group-addon">New:</span>
							<input type="text" id="new_stopword" value="" class="form-control" placeholder="New stopword"> 
							<span class="input-group-btn">
								<button class="btn btn-info" onclick="add_stopword($(`#new_stopword`).val(), true)">Add</button>
							</span>
						</div>
					</div>
				</div>
				<div class="scrolling_list" id="div_stopwords" style="background-color:#ece9e6; color:#b00000;"></div>
			<?php 
			}
			else
			if ($_GET['page'] == 'work') { ?>
				<h1>Work</h1>
				
				<label class="scrolling_list_label">Found messages:</label>
				<div class="scrolling_list" style="max-height: 400px;" id="div_messages"></div>
				<label class="scrolling_list_label">Log:</label>
				<div class="scrolling_list" id="div_log">
				</div>
			<?php 
			} else {?>
				<h1>Login</h1>
				
				<form method="post" class="form-horizontal">
					<input type="hidden" name="login_submitted" value="1">
					<div class="row">
						<label class="control-label col-md-4">User name:</label>
						<div class="col-md-8"><input type="text" class="form-control" name="login_name"></div>
					</div>
					<div class="row">
						<label class="control-label col-md-4">Password:</label>
						<div class="col-md-8"><input type="password" class="form-control" name="password"></div>
					</div>
					<div class="row">
						<button class="btn btn-primary btn-lg" style="display: block; margin: auto;">Login...</button>
					</div>
				</form>
			<?php
			} ?>

		</div>
	</div>

	<script type="text/javascript">
	function change_group_status(group_id)
	{
		$.ajax({
			method: "GET",
			url: "/",
			data: {command:"change_group_status", group_id: group_id, group_status: $("input[name='group_" + group_id + "']:checked").val()}
		})
		.done(function( ajax__result ) {
			var arr_ajax__result = JSON.parse(ajax__result);
		});
	}
	
	function refersh_groups()
	{
		try {
			$.ajax({
				method: "GET",
				url: "/",
				data: {command:"get_list_of_groups"}
			})
			.done(function( ajax__result ) {
				var arr_ajax__result = JSON.parse(ajax__result);
				if ( arr_ajax__result["success"] ) {
					$("#table_groups").html("");
					groups_arr = arr_ajax__result["values"];
					var table_html = "";
					for (var i = 0; i < groups_arr.length; i++) {
						table_html = table_html +
						`
						<tr>
						<td>${groups_arr[i]["group_name"]}</td>
						<td><div class="radio"><label><input type="radio" name="group_${groups_arr[i]["group_id"]}" value="i" ${groups_arr[i]["group_status"] == "i" ? "checked" : ""} onclick="change_group_status('${groups_arr[i]["group_id"]}')">ignore</label></div></td>
						<td><div class="radio"><label><input type="radio" name="group_${groups_arr[i]["group_id"]}" value="l" ${groups_arr[i]["group_status"] == "l" ? "checked" : ""} onclick="change_group_status('${groups_arr[i]["group_id"]}')">listen</label></div></td>
						<td><div class="radio"><label><input type="radio" name="group_${groups_arr[i]["group_id"]}" value="a" ${groups_arr[i]["group_status"] == "a" ? "checked" : ""} onclick="change_group_status('${groups_arr[i]["group_id"]}')">admins</label></div></td>
						</tr>
						`;
					}
					$("#table_groups").html( `<table class="table table-striped">${table_html}</table>` );
				}
			});
		}
		catch(error){}
	}
	
	function read_keywords()
	{
		try {
			$.ajax({
				method: "GET",
				url: "/",
				data: {command:"get_keywords"}
			})
			.done(function( ajax__result ) {
				var arr_ajax__result = JSON.parse(ajax__result);
				if ( arr_ajax__result["success"] ) {
					$("#div_keywords").html("");
					arr = JSON.parse(arr_ajax__result["values"]);
					var table_html = "";
					for (var i = 0; i < arr.length; i++) {
						var keyw = Base64.decode(arr[i]);
						table_html = table_html +
						`
						<tr>
							<td class="keyword_name">${keyw}</td><td class="keyword_remove"><a href="add" onclick="delete_keyword('${keyw}'); return false;">remove</a></td>
						</tr>
						`;
					}
					$("#div_keywords").html( `<table class="table table-striped" id="table_keywords">${table_html}</table>` );
				}
			});
		}
		catch(error){}
	}
	
	function save_keywords()
	{
		try {
			var keyword_arr = [];
			$(".keyword_name").each(function( index ) {
				keyword_arr.push( $(this).html() );
			});
			keyword_arr.sort();
			var keyword_json = "";
			for (var i = 0; i < keyword_arr.length; i++) {
				keyword_json = keyword_json + (keyword_json.length > 0 ? "," : "") + '"' + Base64.encode(keyword_arr[i]) + '"';
			}
			keyword_json = Base64.encode(`[${keyword_json}]`);
			$.ajax({
				method: "GET",
				url: "/",
				data: {command:"save_keywords", keywords: keyword_json}
			})
			.done(function( ajax__result ) {
				var arr_ajax__result = JSON.parse(ajax__result);
			});
		}
		catch(error){}
	}

	function add_keyword(keyword)
	{
		$("#table_keywords").html( $("#table_keywords").html() + `<tr><td class="keyword_name">${keyword}</td><td class="keyword_remove"><a href="add" onclick="delete_keyword('${keyword}'); return false;">remove</a></td></tr>` );
		save_keywords();
		var msg = Base64.encode(`Added keyword: ${keyword}`);
		var log_msg = Base64.encode(`{"message" : "${msg}", "color" : "O", "unixtime" : "${Math.floor(Date.now() / 1000)}"}`);
		$.ajax({
			method: "GET",
			url: "/",
			data: {command:"add_log", log: log_msg}
		})
		.done(function( ajax__result ) {
			var arr_ajax__result = JSON.parse(ajax__result);
		});
	}
	
	function delete_keyword(keyword)
	{
		$('#table_keywords tr').each(function( index ) {
			var td = $(this).children('td:first');
			if ( td.html() == keyword) {
				$(this).remove();
			}
		});
		save_keywords();

		var log_msg = Base64.encode(`{"message" : "${Base64.encode(`Removed keyword: ${keyword}`)}", "color" : "O", "unixtime" : "${Math.floor(Date.now() / 1000)}"}`);
		$.ajax({
			method: "GET",
			url: "/",
			data: {command:"add_log", log: log_msg}
		})
		.done(function( ajax__result ) {
			var arr_ajax__result = JSON.parse(ajax__result);
		});
	}
	
	
	function read_stopwords()
	{
		try {
			$.ajax({
				method: "GET",
				url: "/",
				data: {command:"get_stopwords"}
			})
			.done(function( ajax__result ) {
				var arr_ajax__result = JSON.parse(ajax__result);
				if ( arr_ajax__result["success"] ) {
					$("#div_stopwords").html("");
					arr = JSON.parse(arr_ajax__result["values"]);
					var table_html = "";
					for (var i = 0; i < arr.length; i++) {
						var stopw = Base64.decode(arr[i]);
						table_html = table_html +
						`
						<tr>
							<td class="stopword_name">${stopw}</td><td class="stopword_remove"><a href="add" onclick="delete_stopword('${stopw}'); return false;">remove</a></td>
						</tr>
						`;
					}
					$("#div_stopwords").html( `<table class="table table-striped" id="table_stopwords">${table_html}</table>` );
				}
			});
		}
		catch(error){}
	}
	
	function save_stopwords()
	{
		try {
			var stopword_arr = [];
			$(".stopword_name").each(function( index ) {
				stopword_arr.push( $(this).html() );
			});
			stopword_arr.sort();
			var stopword_json = "";
			for (var i = 0; i < stopword_arr.length; i++) {
				stopword_json = stopword_json + (stopword_json.length > 0 ? "," : "") + '"' + Base64.encode(stopword_arr[i]) + '"';
			}
			stopword_json = Base64.encode(`[${stopword_json}]`);
			$.ajax({
				method: "GET",
				url: "/",
				data: {command:"save_stopwords", stopwords: stopword_json}
			})
			.done(function( ajax__result ) {
				var arr_ajax__result = JSON.parse(ajax__result);
			});
		}
		catch(error){}
	}

	function add_stopword(stopword)
	{
		$("#table_stopwords").html( $("#table_stopwords").html() + `<tr><td class="stopword_name">${stopword}</td><td class="stopword_remove"><a href="add" onclick="delete_stopword('${stopword}'); return false;">remove</a></td></tr>` );
		save_stopwords();

		$.ajax({
			method: "GET",
			url: "/",
			data: {command:"add_log", log: Base64.encode(`{"message" : "${Base64.encode(`Added stop word: ${stopword}`)}", "color" : "O", "unixtime" : "${Math.floor(Date.now() / 1000)}"}`)}
		})
		.done(function( ajax__result ) {
			var arr_ajax__result = JSON.parse(ajax__result);
		});
	}
	
	function delete_stopword(stopword)
	{
		$('#table_stopwords tr').each(function( index ) {
			var td = $(this).children('td:first');
			if ( td.html() == stopword) {
				$(this).remove();
			}
		});
		save_stopwords();

		$.ajax({
			method: "GET",
			url: "/",
			data: {command:"add_log", log: Base64.encode(`{"message" : "${Base64.encode(`Deleted stop word: ${stopword}`)}", "color" : "O", "unixtime" : "${Math.floor(Date.now() / 1000)}"}`)}
		})
		.done(function( ajax__result ) {
			var arr_ajax__result = JSON.parse(ajax__result);
		});
	}
	
	function read_messages()
	{
		try {
			$.ajax({
				method: "GET",
				url: "/",
				data: {command:"get_messages"}
			})
			.done(function( ajax__result ) {
				var arr_ajax__result = JSON.parse(ajax__result);
				if ( arr_ajax__result["success"] ) {
					$("#div_messages").html("");
					arr = JSON.parse(arr_ajax__result["values"]);
					var table_html = "";
					for (var i = 0; i < arr.length; i++) {
						var value = Base64.decode(arr[i]["message"]);
						table_html = table_html +
						`
						<tr>
							<td>${value}</td>
						</tr>
						`;
					}
					$("#div_messages").html( `<table class="table table-striped" id="table_messages">${table_html}</table>` );
				}
			});
		}
		catch(error){}
	}

	function get_log()
	{
		try {
			$.ajax({
				method: "GET",
				url: "/",
				data: {command:"get_log"}
			})
			.done(function( ajax__result ) {
				var arr_ajax__result = JSON.parse(ajax__result);
				if ( arr_ajax__result["success"] ) {
					$("#div_log").html("");
					arr = JSON.parse(arr_ajax__result["values"]);
					var table_html = "";
					for (var i = 0; i < arr.length; i++) {
						var value = Base64.decode(arr[i]["message"]);
						var date = new Date(arr[i]["unixtime"] * 1000);
						var log_color = "#419f41";
						switch (arr[i]["color"]) {
							case 'R':
								log_color = "#bc3232";
								break;
							case 'O':
								log_color = "#c27400";
								break;
							default:
								log_color = "#419f41";
						}

						table_html = table_html +
						`
						<tr style="color:${log_color}">
							<td class="log_td_time" style="vertical-align: middle;">${date.toLocaleString()}</td><td style="width:100%">${value}</td>
						</tr>
						`;
					}
					$("#div_log").html( `<table class="table table-striped" id="table_log">${table_html}</table>` );
				}
			});
		}
		catch(error){}
	}

	$( document ).ready(function() {
		refersh_groups();
		read_keywords();
		read_stopwords();
		read_messages();
		get_log();
		setInterval(refersh_groups, 5000);
		setInterval(read_messages, 2000);
		setInterval(get_log, 5000);
	});
	</script>
	</body>
</html>
