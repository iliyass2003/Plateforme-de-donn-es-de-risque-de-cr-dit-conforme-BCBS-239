# Télécharge les données Home Credit dans data/source (ignoré par Git).
$dest = "data\source"
New-Item -ItemType Directory -Path $dest -Force | Out-Null

kaggle competitions download -c home-credit-default-risk -p $dest
Expand-Archive "$dest\home-credit-default-risk.zip" -DestinationPath $dest -Force
Remove-Item "$dest\home-credit-default-risk.zip"

Get-ChildItem $dest -Filter *.csv |
  Select-Object Name, @{ Name = "Taille_Mo"; Expression = { [math]::Round($_.Length / 1MB) } }