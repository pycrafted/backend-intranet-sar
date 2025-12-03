-- ============================================================================
-- Script SQL pour nettoyer les orphelins restants du forum
-- ============================================================================
-- Ce script nettoie les enregistrements restants après la première exécution
-- qui a échoué partiellement à cause de l'ordre de suppression
-- ============================================================================

BEGIN;

-- ============================================================================
-- ÉTAPE 1 : Supprimer les permissions restantes liées au forum
-- ============================================================================
-- Supprimer les permissions qui référencent des content types du forum
DELETE FROM auth_permission 
WHERE content_type_id IN (
    SELECT id FROM django_content_type WHERE app_label = 'forum'
);

-- ============================================================================
-- ÉTAPE 2 : Supprimer les logs d'administration liés au forum
-- ============================================================================
-- Supprimer les logs d'administration qui référencent des content types du forum
DELETE FROM django_admin_log 
WHERE content_type_id IN (
    SELECT id FROM django_content_type WHERE app_label = 'forum'
);

-- Alternative : Si les content types n'existent plus (ID 29 dans votre cas),
-- supprimer directement par ID
DELETE FROM django_admin_log WHERE content_type_id = 29;

-- ============================================================================
-- ÉTAPE 3 : Supprimer les content types restants du forum
-- ============================================================================
DELETE FROM django_content_type 
WHERE app_label = 'forum';

-- ============================================================================
-- ÉTAPE 4 : Vérifier et supprimer les migrations restantes
-- ============================================================================
DELETE FROM django_migrations 
WHERE app = 'forum';

-- ============================================================================
-- VÉRIFICATION
-- ============================================================================
-- Vérifier qu'il ne reste plus de content types forum
SELECT 'Content types restants:' as info, COUNT(*) as count
FROM django_content_type 
WHERE app_label = 'forum';

-- Vérifier qu'il ne reste plus de permissions orphelines
-- (permissions qui référencent des content types inexistants)
SELECT 'Permissions orphelines:' as info, COUNT(*) as count
FROM auth_permission ap
LEFT JOIN django_content_type ct ON ap.content_type_id = ct.id
WHERE ct.id IS NULL;

-- Vérifier qu'il ne reste plus de logs d'administration orphelins
SELECT 'Logs admin orphelins:' as info, COUNT(*) as count
FROM django_admin_log al
LEFT JOIN django_content_type ct ON al.content_type_id = ct.id
WHERE ct.id IS NULL;

-- Vérifier qu'il ne reste plus de migrations forum
SELECT 'Migrations restantes:' as info, COUNT(*) as count
FROM django_migrations 
WHERE app = 'forum';

COMMIT;

-- ============================================================================
-- FIN DU SCRIPT
-- ============================================================================

