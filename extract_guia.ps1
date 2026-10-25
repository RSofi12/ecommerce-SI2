Add-Type -AssemblyName System.IO.Compression.FileSystem
$docxFile = (Get-ChildItem -Path . -Filter "*GUIA*TEOR*Informe*SI-2*.docx").FullName
Write-Output "Found: $docxFile"
$zip = [System.IO.Compression.ZipFile]::OpenRead($docxFile)
$entry = $zip.GetEntry("word/document.xml")
$stream = $entry.Open()
$reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::UTF8)
$xmlText = $reader.ReadToEnd()
$reader.Close()
$stream.Close()
$zip.Dispose()

[xml]$doc = $xmlText
$ns = New-Object System.Xml.XmlNamespaceManager($doc.NameTable)
$ns.AddNamespace("w", "http://schemas.openxmlformats.org/wordprocessingml/2006/main")
$nodes = $doc.SelectNodes("//w:p", $ns)
$lines = [System.Collections.Generic.List[string]]::new()
foreach ($p in $nodes) {
    $tNodes = $p.SelectNodes(".//w:t", $ns)
    $text = ""
    foreach ($t in $tNodes) { 
        $text += $t.InnerText 
    }
    if ($text.Trim() -ne "") { 
        $lines.Add($text) 
    }
}
[System.IO.File]::WriteAllLines("extracted_guia_teoria.txt", $lines, [System.Text.Encoding]::UTF8)
Write-Output "Done. Paragraph count: $($lines.Count)"
