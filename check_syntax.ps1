$filePath = '.\frontend\index.html'
if (Test-Path $filePath) {
    $content = Get-Content $filePath -Raw
    $openCurly = [regex]::Matches($content, '\{').Count
    $closeCurly = [regex]::Matches($content, '\}').Count
    $openParen = [regex]::Matches($content, '\(').Count
    $closeParen = [regex]::Matches($content, '\)').Count
    $openSquare = [regex]::Matches($content, '\[').Count
    $closeSquare = [regex]::Matches($content, '\]').Count
    $openAngle = [regex]::Matches($content, '<').Count
    $closeAngle = [regex]::Matches($content, '>').Count
    $doubleQuotes = [regex]::Matches($content, '"').Count
    $singleQuotes = [regex]::Matches($content, "'").Count
    
    Write-Host '=== SYNTAX CHECK RESULTS ==='
    Write-Host ('Curly Braces: {0} / {1} {2}' -f $openCurly, $closeCurly, (if($openCurly -eq $closeCurly) {'OK'} else {'MISMATCH'}))
    Write-Host ('Parentheses: {0} / {1} {2}' -f $openParen, $closeParen, (if($openParen -eq $closeParen) {'OK'} else {'MISMATCH'}))
    Write-Host ('Square Brackets: {0} / {1} {2}' -f $openSquare, $closeSquare, (if($openSquare -eq $closeSquare) {'OK'} else {'MISMATCH'}))
    Write-Host ('Angle Brackets: {0} / {1} {2}' -f $openAngle, $closeAngle, (if($openAngle -eq $closeAngle) {'OK'} else {'MISMATCH'}))
    Write-Host ('Double Quotes: {0} {1}' -f $doubleQuotes, (if($doubleQuotes % 2 -eq 0) {'OK (even)'} else {'MISMATCH (odd)'}))
    Write-Host ('Single Quotes: {0} {1}' -f $singleQuotes, (if($singleQuotes % 2 -eq 0) {'OK (even)'} else {'MISMATCH (odd)'}))
} else {
    Write-Host 'File not found!'
}
