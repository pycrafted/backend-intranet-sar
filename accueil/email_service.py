"""
Service d'envoi d'emails pour la boîte à idées
Utilise le serveur SMTP Exchange de la SAR
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)

# Configuration SMTP Exchange
SMTP_CONFIG = {
    "host": "sar-sn.mail.protection.outlook.com",
    "port": 25,
    "use_tls": True,
    "auth_required": False,  # Relais SMTP ne nécessite pas d'auth
}

SMTP_USER = "notification@sar.sn"


def send_idea_email(
    idea_description: str,
    department_name: str,
    recipient_emails: List[str],
    idea_id: Optional[int] = None
) -> bool:
    """
    Envoie un email anonyme contenant une idée au chef de département
    
    Args:
        idea_description: Description de l'idée
        department_name: Nom du département concerné
        recipient_emails: Liste des emails des destinataires (chefs de département)
        idea_id: ID de l'idée (optionnel, pour référence)
    
    Returns:
        True si l'email a été envoyé avec succès, False sinon
    """
    if not recipient_emails:
        logger.warning(f"Aucun email destinataire pour le département {department_name}")
        return False
    
    # Filtrer les emails valides
    valid_emails = [email for email in recipient_emails if email and '@' in email]
    if not valid_emails:
        logger.warning(f"Aucun email valide pour le département {department_name}")
        return False
    
    try:
        # Création du message
        msg = MIMEMultipart('alternative')
        msg['From'] = SMTP_USER
        msg['To'] = ', '.join(valid_emails)
        msg['Subject'] = f"Nouvelle idée - {department_name}"
        
        # Date de soumission
        submission_date = datetime.now().strftime('%d/%m/%Y à %H:%M')
        
        # Corps du message en texte brut
        text_content = f"""Bonjour,

Une nouvelle idée a été soumise via la Boîte à Idées de l'intranet SAR.

Structure concernée: {department_name}
Date de soumission: {submission_date}
{f"Référence: Idée #{idea_id}" if idea_id else ""}

Idée soumise:

{idea_description}

---
Cet email a été envoyé automatiquement depuis l'intranet SAR.

L'idée a été soumise de manière anonyme."""
        
        # Corps du message en HTML - Design professionnel et sobre
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, Helvetica, sans-serif; font-size: 14px; line-height: 1.6; color: #000000; background-color: #f5f5f5; margin: 0; padding: 0;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border: 1px solid #dddddd;">
                    <tr>
                        <td style="padding: 30px;">
                            <p style="margin: 0 0 20px 0; font-size: 14px;">
                                Bonjour,
                            </p>
                            
                            <p style="margin: 0 0 20px 0; font-size: 14px;">
                                Une nouvelle idée a été soumise via la Boîte à Idées de l'intranet SAR.
                            </p>
                            
                            <p style="margin: 10px 0; font-size: 14px;">
                                <strong>Structure concernée:</strong> {department_name}
                            </p>
                            
                            <p style="margin: 10px 0; font-size: 14px;">
                                <strong>Date de soumission:</strong> {submission_date}
                            </p>
                            
                            {f'<p style="margin: 10px 0; font-size: 14px;"><strong>Référence:</strong> Idée #{idea_id}</p>' if idea_id else ''}
                            
                            <p style="margin: 20px 0 10px 0; font-size: 14px;">
                                <strong>Idée soumise:</strong>
                            </p>
                            
                            <p style="margin: 0 0 30px 0; font-size: 14px; white-space: pre-wrap; line-height: 1.8;">
{idea_description}
                            </p>
                            
                            <p style="margin: 30px 0 5px 0; padding-top: 20px; border-top: 1px solid #dddddd; font-size: 12px; color: #666666;">
                                Cet email a été envoyé automatiquement depuis l'intranet SAR.
                            </p>
                            
                            <p style="margin: 0; font-size: 12px; color: #666666;">
                                L'idée a été soumise de manière anonyme.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
        
        # Attacher les deux versions
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part1)
        msg.attach(part2)
        
        # Connexion et envoi
        logger.info(f"📧 Tentative d'envoi d'email pour l'idée #{idea_id} au département {department_name}")
        logger.info(f"   Destinataires: {', '.join(valid_emails)}")
        
        server = None
        try:
            # Connexion au serveur SMTP
            server = smtplib.SMTP(SMTP_CONFIG['host'], SMTP_CONFIG['port'], timeout=30)
            server.set_debuglevel(0)
            
            logger.info("✓ Connexion SMTP établie")
            
            # Activer TLS si nécessaire
            if SMTP_CONFIG['use_tls']:
                server.starttls()
                logger.info("✓ STARTTLS activé")
            
            # Envoi de l'email
            logger.info("📤 Envoi de l'email...")
            refused = server.send_message(msg, to_addrs=valid_emails)
            
            if refused:
                logger.warning(f"⚠️  Certains destinataires ont été refusés: {refused}")
                return False
            else:
                logger.info("✓ Email accepté par le serveur SMTP")
                logger.info("✓ Email mis en file d'attente pour livraison")
                return True
                
        except smtplib.SMTPException as e:
            logger.error(f"❌ Erreur SMTP lors de l'envoi: {e}")
            return False
        except (OSError, ConnectionError, TimeoutError) as e:
            logger.error(f"❌ Erreur de connexion: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur inattendue lors de l'envoi: {e}")
            return False
        finally:
            if server:
                try:
                    server.quit()
                except:
                    pass
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de la préparation de l'email: {e}")
        return False

