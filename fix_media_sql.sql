-- Script SQL pour corriger les noms de fichiers média
-- Ce script corrige les noms de fichiers dans la base de données

-- Afficher les articles avec des images problématiques
SELECT id, image, title 
FROM actualites_article 
WHERE image IS NOT NULL AND image != '';

-- Corriger les noms de fichiers connus
UPDATE actualites_article 
SET image = 'articles/img1.png' 
WHERE image = 'articles/img1_Jxa8Ucl.png';

UPDATE actualites_article 
SET image = 'articles/image_terrain.jpeg' 
WHERE image = 'articles/image_terrain.jpeg' 
AND image NOT LIKE 'articles/image_terrain%';

-- Corriger les autres fichiers avec des suffixes Django
UPDATE actualites_article 
SET image = REPLACE(image, '_Jxa8Ucl', '')
WHERE image LIKE '%_Jxa8Ucl%';

UPDATE actualites_article 
SET image = REPLACE(image, '_JbE14AL', '')
WHERE image LIKE '%_JbE14AL%';

UPDATE actualites_article 
SET image = REPLACE(image, '_CR36IV1', '')
WHERE image LIKE '%_CR36IV1%';

UPDATE actualites_article 
SET image = REPLACE(image, '_h3iXysh', '')
WHERE image LIKE '%_h3iXysh%';

UPDATE actualites_article 
SET image = REPLACE(image, '_KybIco7', '')
WHERE image LIKE '%_KybIco7%';

UPDATE actualites_article 
SET image = REPLACE(image, '_gxSj1VP', '')
WHERE image LIKE '%_gxSj1VP%';

-- Vérifier les corrections
SELECT id, image, title 
FROM actualites_article 
WHERE image IS NOT NULL AND image != '';

