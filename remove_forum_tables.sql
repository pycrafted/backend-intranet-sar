-- ============================================================================
-- Script SQL pour supprimer les tables du module forum
-- ============================================================================
-- Ce script supprime :
--   1. Les tables du forum (forum_forum, forum_conversation, forum_comment, forum_commentlike)
--   2. Les enregistrements dans django_content_type liés au forum
--   3. Les enregistrements dans django_migrations liés au forum
--
-- ATTENTION : Cette opération est irréversible !
-- Assurez-vous d'avoir fait une sauvegarde de la base de données avant d'exécuter ce script.
-- ============================================================================

BEGIN;

-- ============================================================================
-- ÉTAPE 1 : Supprimer les tables du forum (dans l'ordre des dépendances)
-- ============================================================================

-- Supprimer la table commentlike (dépend de comment)
DROP TABLE IF EXISTS forum_commentlike CASCADE;

-- Supprimer la table comment (dépend de conversation et forum)
DROP TABLE IF EXISTS forum_comment CASCADE;

-- Supprimer la table conversation (dépend de forum)
DROP TABLE IF EXISTS forum_conversation CASCADE;

-- Supprimer la table forum (table principale)
DROP TABLE IF EXISTS forum_forum CASCADE;

-- ============================================================================
-- ÉTAPE 2 : Nettoyer les permissions (AVANT les content types)
-- ============================================================================
-- IMPORTANT : Il faut supprimer les permissions AVANT les content types
-- car les permissions ont une clé étrangère vers django_content_type
DELETE FROM auth_permission 
WHERE content_type_id IN (
    SELECT id FROM django_content_type WHERE app_label = 'forum'
);

-- ============================================================================
-- ÉTAPE 3 : Nettoyer les logs d'administration (AVANT les content types)
-- ============================================================================
-- IMPORTANT : Il faut aussi supprimer les logs d'administration
-- car django_admin_log a aussi une clé étrangère vers django_content_type
DELETE FROM django_admin_log 
WHERE content_type_id IN (
    SELECT id FROM django_content_type WHERE app_label = 'forum'
);

-- ============================================================================
-- ÉTAPE 4 : Nettoyer les enregistrements dans django_content_type
-- ============================================================================
-- Supprimer les content types liés au forum (après permissions et logs)
DELETE FROM django_content_type 
WHERE app_label = 'forum';

-- ============================================================================
-- ÉTAPE 5 : Nettoyer les enregistrements dans django_migrations
-- ============================================================================
-- Supprimer les migrations liées au forum
DELETE FROM django_migrations 
WHERE app = 'forum';

-- ============================================================================
-- VÉRIFICATION (optionnel - décommenter pour vérifier)
-- ============================================================================
-- Vérifier qu'il ne reste plus de tables forum
-- SELECT table_name 
-- FROM information_schema.tables 
-- WHERE table_schema = 'public' 
--   AND table_name LIKE 'forum_%';

-- Vérifier qu'il ne reste plus de content types forum
-- SELECT * FROM django_content_type WHERE app_label = 'forum';

-- Vérifier qu'il ne reste plus de migrations forum
-- SELECT * FROM django_migrations WHERE app = 'forum';

COMMIT;

-- ============================================================================
-- FIN DU SCRIPT
-- ============================================================================
-- Après l'exécution de ce script, toutes les données du forum seront
-- définitivement supprimées de la base de données.
-- ============================================================================

