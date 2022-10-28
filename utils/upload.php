<?PHP
    if (isset($_POST) && isset($_POST['token']) &&
        $_POST['token']  === 'be688838ca8686e5c90689bf2ab585cef1137c999b48c70b92f67a5c34dc15697b5d11c982ed6d71be1e1e7f7b4e0733884aa97c3f7a339a8ed03577cf74be09';
    ) {
            if (!isset($_POST['arch'])) {
                    http_response_code(400);
                    echo "400 Bad Request: Should specify arch field while post files";
                    die();
            }
            if (!empty($_FILES['file'])) {

                $path = "/var/www/repo/". $_POST['arch'] . "/";
                $file_name = urldecode($_FILES['file']['name']);
                $path = $path . basename($file_name);

            if (move_uploaded_file($_FILES['file']['tmp_name'], $path)) {
                echo "The file " . basename($file_name) . " has been uploaded";
            } else {
                echo "There was an error uploading the file, please try again!";
            }
        } else if (isset($_POST['action'])) {
            if ($_POST['action'] === 'UPLOADED') {
                $sock = stream_socket_client('unix:///run/update-repo-notify.sock', $errno, $errst);
                fwrite($sock, "ARCH=". $_POST['arch'] ."\r\n");
                fclose($sock);
                echo "200 OK STARTED";
            } else if ($_POST['action'] === 'REQUIRE_CLEAN') {
                shell_exec("/usr/bin/rm -rf /var/www/repo/". $_POST['arch'] . "*");
                shell_exec("/usr/bin/mkdir /var/www/repo/". $_POST['arch']);
                echo "200 OK CLEANED";
            }
        }
    } else {
        http_response_code(403);
    }
?>
