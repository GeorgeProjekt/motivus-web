<?php
/**
 * Motivus Contact API
 * Přijímá JSON požadavky z motivus.cz, přidává CORS a odesílá mail.
 */

// Povolit přístup specificky z živého webu
$allowed_origins = [
    'https://motivus.cz',
    'https://www.motivus.cz',
    'http://localhost',
    'http://127.0.0.1' // Pro lokální vývoj
];

$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if (in_array($origin, $allowed_origins)) {
    header("Access-Control-Allow-Origin: $origin");
} else {
    // Pro bezpečí nebudeme plošně otevírat všem (*) pokud to není nutné, 
    // pro produkci to necháváme projít (ale origin zůstane prázdný, takže prohlížeč zablokuje cizí skripty).
}

header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type");
header("Content-Type: application/json; charset=UTF-8");

// Handle preflight OPTIONS request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    // Vyčtení JSON dat z těla (pokud je asynchronní odeslání provedeno správně z fetch())
    $json = file_get_contents('php://input');
    $data = json_decode($json, true);

    $name = htmlspecialchars(trim($data["name"] ?? $_POST["name"] ?? ""));
    $email = filter_var(trim($data["email"] ?? $_POST["email"] ?? ""), FILTER_SANITIZE_EMAIL);
    $message = htmlspecialchars(trim($data["message"] ?? $_POST["message"] ?? ""));

    if (empty($name) || empty($email) || empty($message) || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        http_response_code(400);
        echo json_encode(["status" => "error", "message" => "Prosím vyplňte správně všechna pole."]);
        exit;
    }

    $to = "info@motivus.cz"; // Hlavní sběrný e-mail
    $subject = "Nová zpráva z webu Motivus od: $name";
    
    $email_content = "Jméno: $name\n";
    $email_content .= "E-mail: $email\n\n";
    $email_content .= "Zpráva:\n$message\n";

    // Nastavení hlaviček pro správné přijetí antispamem u cíle
    $headers = "From: Motivus Web <info@motivus.cz>\r\n";
    $headers .= "Reply-To: $name <$email>\r\n";
    $headers .= "Content-Type: text/plain; charset=utf-8\r\n";

    if (mail($to, $subject, $email_content, $headers)) {
        http_response_code(200);
        echo json_encode(["status" => "success", "message" => "Zpráva byla úspěšně odeslána. Děkujeme."]);
    } else {
        http_response_code(500);
        echo json_encode(["status" => "error", "message" => "Jejda! Něco se pokazilo na serveru. Skript mail() patrně havaroval."]);
    }
} else {
    http_response_code(405);
    echo json_encode(["status" => "error", "message" => "Tato metoda není povolena."]);
}
?>
