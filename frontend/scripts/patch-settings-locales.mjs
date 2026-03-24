/**
 * One-off: replace SettingsTenant / SettingsPlatform in fr, es, ar, sw, rw.
 * Run: node frontend/scripts/patch-settings-locales.mjs
 */
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const localesDir = path.join(__dirname, "..", "public", "locales");

const fr = {
  SettingsTenant: {
    tenant: {
      page: {
        title: "Paramètres du locataire",
        description: "Gérer le profil et l’image de marque de votre organisation",
      },
      loadError: "Impossible de charger les informations du locataire",
      toast: {
        updated: "Paramètres du locataire mis à jour",
        updateFailed: "Échec de la mise à jour des paramètres du locataire",
      },
      profile: {
        title: "Profil",
        description: "Mettre à jour le nom et l’image de marque du locataire",
      },
      reset: "Réinitialiser",
      save: "Enregistrer les modifications",
      saving: "Enregistrement…",
      form: {
        tenantName: "Nom du locataire",
        siteName: "Nom du site",
        primaryColor: "Couleur principale",
        colorPickerAria: "Choisir la couleur principale",
        placeholderOrg: "Mon organisation",
        placeholderSite: "Portail inventaire",
        placeholderColor: "#3B82F6",
        requiredMarker: "obligatoire",
      },
      validation: {
        nameRequired: "Le nom du locataire est obligatoire",
        hexColor: "Doit être une couleur hexadécimale valide (ex. #3B82F6)",
      },
    },
    subscription: {
      title: "Abonnement",
      description: "Votre offre actuelle et l’utilisation",
      planLabel: "Offre",
      usageUsers: "Utilisateurs",
      usageProducts: "Produits",
    },
    roles: {
      owner: "Propriétaire",
      admin: "Administrateur",
      manager: "Gestionnaire",
      viewer: "Lecteur",
    },
    plans: {
      free: "Gratuit",
      starter: "Starter",
      professional: "Professionnel",
      enterprise: "Entreprise",
    },
    subscriptionStatus: {
      active: "Actif",
      trial: "Essai",
      past_due: "En retard",
      cancelled: "Annulé",
      suspended: "Suspendu",
    },
    members: {
      page: {
        title: "Membres de l’équipe",
        description: "Gérer les membres et leurs rôles",
      },
      searchPlaceholder: "Rechercher des membres…",
      emptyMessage: "Aucun membre d’équipe trouvé.",
      toast: {
        roleUpdated: "Rôle de {username} mis à jour : {role}",
        roleFailed: "Échec de la mise à jour du rôle",
        removed: "{username} a été retiré de l’équipe",
        removeFailed: "Échec du retrait du membre",
      },
      removeDialog: {
        title: "Retirer un membre",
        descriptionLead: "Voulez-vous vraiment retirer",
        descriptionTrail:
          "de l’équipe ? Il perdra immédiatement l’accès à ce locataire.",
      },
      remove: "Retirer",
      removing: "Retrait…",
      columns: {
        user: "Utilisateur",
        email: "E-mail",
        role: "Rôle",
        status: "Statut",
        joined: "Inscrit le",
      },
      memberStatus: { active: "Actif", inactive: "Inactif" },
      srRemoveMember: "Retirer le membre",
    },
    invite: {
      trigger: "Inviter un membre",
      title: "Inviter un membre de l’équipe",
      description:
        "Envoyer une invitation par e-mail. Un lien pour rejoindre votre organisation sera envoyé.",
      email: "Adresse e-mail",
      role: "Rôle",
      placeholderEmail: "collegue@entreprise.com",
      sendInvitation: "Envoyer l’invitation",
      sending: "Envoi…",
      toastSent: "Invitation envoyée à {email}",
      toastFailed: "Échec de l’envoi de l’invitation",
    },
    pendingInvitations: {
      heading: "Invitations en attente",
      headingCount: "({count})",
      columns: {
        email: "E-mail",
        role: "Rôle",
        status: "Statut",
        expires: "Expire",
      },
      srCancelInvitation: "Annuler l’invitation",
      cancelDialog: {
        title: "Annuler l’invitation",
        descriptionLead: "Voulez-vous vraiment annuler l’invitation pour",
        descriptionTrail: " ? Le lien d’invitation ne fonctionnera plus.",
      },
      keep: "Conserver",
      cancelInvitation: "Annuler l’invitation",
      cancelling: "Annulation…",
      toastCancelled: "Invitation pour {email} annulée",
      toastCancelFailed: "Échec de l’annulation de l’invitation",
      invitationStatus: {
        pending: "En attente",
        accepted: "Acceptée",
        cancelled: "Annulée",
        expired: "Expirée",
      },
    },
    acceptInvitation: {
      invalidTitle: "Invitation invalide",
      invalidDescription:
        "Ce lien d’invitation est invalide, expiré ou a déjà été utilisé.",
      goToLogin: "Aller à la connexion",
      alreadyTitle: "Invitation {status}",
      alreadyDescription: "Cette invitation a déjà été {status}.",
      joinTitle: "Rejoindre {tenant}",
      invitedPrefix: "Vous êtes invité à rejoindre en tant que",
      invitationFor: "Invitation pour",
      firstName: "Prénom",
      lastName: "Nom",
      username: "Nom d’utilisateur",
      password: "Mot de passe",
      placeholderFirst: "Marie",
      placeholderLast: "Dupont",
      placeholderUsername: "mdupont",
      placeholderPasswordNew: "Min. 8 caractères",
      existingAccountHint:
        "Un compte existe déjà avec cet e-mail. Saisissez votre mot de passe pour confirmer votre identité et rejoindre l’organisation.",
      existingPassword: "Mot de passe",
      placeholderExistingPassword: "Votre mot de passe",
      joining: "Adhésion…",
      joinAction: "Rejoindre {tenant}",
      expires: "Expire le {date}",
      acceptFailed: "Échec de l’acceptation de l’invitation",
    },
  },
  SettingsPlatform: {
    billing: {
      page: {
        title: "Facturation et abonnements",
        description:
          "Gérer les offres, l’utilisation et la facturation des locataires (superutilisateur uniquement)",
      },
      columns: {
        tenant: "Locataire",
        plan: "Offre",
        status: "Statut",
        active: "Actif",
        usage: "Utilisation",
      },
      yes: "Oui",
      no: "Non",
      usageUsers: "{current}/{max} utilisateurs",
      usageProducts: "{current}/{max} produits",
      searchPlaceholder: "Rechercher des locataires…",
      emptyMessage: "Aucun locataire trouvé.",
      ariaExport: "Exporter les données du locataire",
      ariaChangePlan: "Changer d’offre",
      ariaSuspend: "Suspendre",
      ariaReactivate: "Réactiver",
      toast: {
        suspended: "{name} a été suspendu",
        suspendFailed: "Échec de la suspension du locataire",
        reactivated: "{name} a été réactivé",
        reactivateFailed: "Échec de la réactivation du locataire",
        exportSuccess: "Export pour {name} téléchargé",
        exportFailed: "Échec de l’export des données du locataire",
        subscriptionUpdated: "Abonnement mis à jour",
        subscriptionUpdateFailed: "Échec de la mise à jour de l’abonnement",
      },
      suspendDialog: {
        title: "Suspendre le locataire",
        descriptionLead: "Voulez-vous vraiment suspendre",
        descriptionTrail:
          " ? Le locataire ne pourra pas se connecter ni accéder aux données tant qu’il n’est pas réactivé.",
      },
      reactivateDialog: {
        title: "Réactiver le locataire",
        descriptionLead: "Voulez-vous vraiment réactiver",
        descriptionTrail:
          " ? Le locataire pourra à nouveau se connecter et accéder aux données.",
      },
      suspend: "Suspendre",
      suspending: "Suspension…",
      reactivate: "Réactiver",
      reactivating: "Réactivation…",
      changePlan: {
        title: "Changer d’offre — {name}",
        description:
          "Mettre à jour l’offre, le statut ou les notes de facturation.",
        plan: "Offre",
        status: "Statut",
        billingNotes: "Notes de facturation (facultatif)",
        billingNotesPlaceholder:
          "Problèmes de paiement, arrangements personnalisés, etc.",
      },
    },
    users: {
      page: {
        title: "Utilisateurs de la plateforme",
        description:
          "Gérer tous les utilisateurs sur les locataires (superutilisateur uniquement)",
      },
      createUser: "Créer un utilisateur",
      searchPlaceholder: "Rechercher par e-mail ou nom d’utilisateur…",
      emptyMessage: "Aucun utilisateur trouvé.",
      columns: {
        user: "Utilisateur",
        email: "E-mail",
        status: "Statut",
        tenants: "Locataires",
        joined: "Inscrit le",
      },
      userStatus: { active: "Actif", suspended: "Suspendu" },
      moreTenants: "+{count}",
      ariaImpersonate: "Usurper l’identité",
      ariaResetPassword: "Réinitialiser le mot de passe",
      ariaSuspendUser: "Suspendre l’utilisateur",
      toast: {
        userSuspended: "{username} a été suspendu",
        suspendFailed: "Échec de la suspension de l’utilisateur",
        passwordReset: "Le mot de passe a été réinitialisé",
        passwordResetFailed: "Échec de la réinitialisation du mot de passe",
        impersonating: "Usurpation de {username}",
        impersonateFailed: "Échec de l’usurpation",
        userCreated: "Utilisateur {username} créé",
        createFailed: "Échec de la création de l’utilisateur",
      },
      suspendDialog: {
        title: "Suspendre l’utilisateur",
        descriptionLead: "Voulez-vous vraiment suspendre",
        descriptionTrail:
          " ? Il perdra l’accès à tous les locataires. Vous pourrez annuler en modifiant l’utilisateur.",
      },
      resetPassword: {
        title: "Réinitialiser le mot de passe",
        description:
          "Saisissez un nouveau mot de passe pour cet utilisateur. Minimum 8 caractères.",
        newPassword: "Nouveau mot de passe",
        placeholder: "Min. 8 caractères",
        resetting: "Réinitialisation…",
        reset: "Réinitialiser",
      },
      createDialog: {
        title: "Créer un utilisateur",
        description:
          "Créer un nouvel utilisateur et éventuellement l’assigner à des locataires.",
        username: "Nom d’utilisateur",
        email: "E-mail",
        password: "Mot de passe",
        defaultRole: "Rôle par défaut (pour les locataires assignés)",
        assignTenants: "Assigner à des locataires",
        placeholderUsername: "jdoe",
        placeholderEmail: "marie@exemple.com",
        placeholderPassword: "Min. 8 caractères",
        creating: "Création…",
        create: "Créer",
      },
    },
    invitations: {
      page: {
        title: "Invitations",
        description:
          "Toutes les invitations des locataires sur la plateforme. Superutilisateur uniquement.",
      },
      emptyMessage: "Aucune invitation trouvée.",
      filterAllStatuses: "Tous les statuts",
      filterStatusPlaceholder: "Statut",
      filterAllTenants: "Tous les locataires",
      filterTenantPlaceholder: "Locataire",
      filterFrom: "Du",
      filterTo: "Au",
      toast: {
        cancelled: "Invitation annulée",
        cancelFailed: "Échec de l’annulation de l’invitation",
        resent: "Invitation renvoyée avec succès",
        resendFailed: "Échec du renvoi de l’invitation",
      },
      columns: {
        email: "E-mail",
        tenant: "Locataire",
        role: "Rôle",
        status: "Statut",
        created: "Créée le",
        expires: "Expire",
        invitedBy: "Invité par",
      },
      rowCancel: "Annuler",
      rowResend: "Renvoyer",
      status: {
        pending: "En attente",
        accepted: "Acceptée",
        cancelled: "Annulée",
        expired: "Expirée",
      },
    },
  },
};

const es = {
  SettingsTenant: {
    tenant: {
      page: {
        title: "Configuración del inquilino",
        description: "Administre el perfil y la marca de su organización",
      },
      loadError: "No se pudo cargar la información del inquilino",
      toast: {
        updated: "Configuración del inquilino actualizada",
        updateFailed: "No se pudo actualizar la configuración del inquilino",
      },
      profile: {
        title: "Perfil",
        description: "Actualice el nombre y la marca del inquilino",
      },
      reset: "Restablecer",
      save: "Guardar cambios",
      saving: "Guardando…",
      form: {
        tenantName: "Nombre del inquilino",
        siteName: "Nombre del sitio",
        primaryColor: "Color principal",
        colorPickerAria: "Elegir color principal",
        placeholderOrg: "Mi organización",
        placeholderSite: "Portal de inventario",
        placeholderColor: "#3B82F6",
        requiredMarker: "obligatorio",
      },
      validation: {
        nameRequired: "El nombre del inquilino es obligatorio",
        hexColor: "Debe ser un color hexadecimal válido (p. ej. #3B82F6)",
      },
    },
    subscription: {
      title: "Suscripción",
      description: "Su plan actual y el uso",
      planLabel: "Plan",
      usageUsers: "Usuarios",
      usageProducts: "Productos",
    },
    roles: {
      owner: "Propietario",
      admin: "Administrador",
      manager: "Gestor",
      viewer: "Lector",
    },
    plans: {
      free: "Gratis",
      starter: "Starter",
      professional: "Profesional",
      enterprise: "Empresa",
    },
    subscriptionStatus: {
      active: "Activo",
      trial: "Prueba",
      past_due: "Vencido",
      cancelled: "Cancelado",
      suspended: "Suspendido",
    },
    members: {
      page: {
        title: "Miembros del equipo",
        description: "Administre miembros y sus roles",
      },
      searchPlaceholder: "Buscar miembros…",
      emptyMessage: "No se encontraron miembros del equipo.",
      toast: {
        roleUpdated: "Rol de {username} actualizado a {role}",
        roleFailed: "No se pudo actualizar el rol",
        removed: "Se eliminó a {username} del equipo",
        removeFailed: "No se pudo eliminar al miembro",
      },
      removeDialog: {
        title: "Eliminar miembro del equipo",
        descriptionLead: "¿Seguro que desea eliminar a",
        descriptionTrail:
          " del equipo? Perderá el acceso a este inquilino de inmediato.",
      },
      remove: "Eliminar",
      removing: "Eliminando…",
      columns: {
        user: "Usuario",
        email: "Correo",
        role: "Rol",
        status: "Estado",
        joined: "Alta",
      },
      memberStatus: { active: "Activo", inactive: "Inactivo" },
      srRemoveMember: "Eliminar miembro",
    },
    invite: {
      trigger: "Invitar miembro",
      title: "Invitar a un miembro del equipo",
      description:
        "Envíe una invitación por correo. Recibirán un enlace para unirse a su organización.",
      email: "Correo electrónico",
      role: "Rol",
      placeholderEmail: "colega@empresa.com",
      sendInvitation: "Enviar invitación",
      sending: "Enviando…",
      toastSent: "Invitación enviada a {email}",
      toastFailed: "No se pudo enviar la invitación",
    },
    pendingInvitations: {
      heading: "Invitaciones pendientes",
      headingCount: "({count})",
      columns: {
        email: "Correo",
        role: "Rol",
        status: "Estado",
        expires: "Vence",
      },
      srCancelInvitation: "Cancelar invitación",
      cancelDialog: {
        title: "Cancelar invitación",
        descriptionLead: "¿Seguro que desea cancelar la invitación para",
        descriptionTrail: "? El enlace dejará de funcionar.",
      },
      keep: "Conservar",
      cancelInvitation: "Cancelar invitación",
      cancelling: "Cancelando…",
      toastCancelled: "Invitación a {email} cancelada",
      toastCancelFailed: "No se pudo cancelar la invitación",
      invitationStatus: {
        pending: "Pendiente",
        accepted: "Aceptada",
        cancelled: "Cancelada",
        expired: "Caducada",
      },
    },
    acceptInvitation: {
      invalidTitle: "Invitación no válida",
      invalidDescription:
        "Este enlace no es válido, expiró o ya se utilizó.",
      goToLogin: "Ir al inicio de sesión",
      alreadyTitle: "Invitación {status}",
      alreadyDescription: "Esta invitación ya está {status}.",
      joinTitle: "Unirse a {tenant}",
      invitedPrefix: "Le invitaron a unirse como",
      invitationFor: "Invitación para",
      firstName: "Nombre",
      lastName: "Apellido",
      username: "Usuario",
      password: "Contraseña",
      placeholderFirst: "Ana",
      placeholderLast: "García",
      placeholderUsername: "agarcia",
      placeholderPasswordNew: "Mín. 8 caracteres",
      existingAccountHint:
        "Ya existe una cuenta con este correo. Introduzca su contraseña para confirmar su identidad y unirse a la organización.",
      existingPassword: "Contraseña",
      placeholderExistingPassword: "Su contraseña",
      joining: "Uniendo…",
      joinAction: "Unirse a {tenant}",
      expires: "Vence el {date}",
      acceptFailed: "No se pudo aceptar la invitación",
    },
  },
  SettingsPlatform: {
    billing: {
      page: {
        title: "Facturación y suscripciones",
        description:
          "Administre planes, uso y facturación de inquilinos (solo superusuario)",
      },
      columns: {
        tenant: "Inquilino",
        plan: "Plan",
        status: "Estado",
        active: "Activo",
        usage: "Uso",
      },
      yes: "Sí",
      no: "No",
      usageUsers: "{current}/{max} usuarios",
      usageProducts: "{current}/{max} productos",
      searchPlaceholder: "Buscar inquilinos…",
      emptyMessage: "No se encontraron inquilinos.",
      ariaExport: "Exportar datos del inquilino",
      ariaChangePlan: "Cambiar plan",
      ariaSuspend: "Suspender",
      ariaReactivate: "Reactivar",
      toast: {
        suspended: "{name} ha sido suspendido",
        suspendFailed: "No se pudo suspender al inquilino",
        reactivated: "{name} ha sido reactivado",
        reactivateFailed: "No se pudo reactivar al inquilino",
        exportSuccess: "Exportación de {name} descargada",
        exportFailed: "No se pudo exportar los datos del inquilino",
        subscriptionUpdated: "Suscripción actualizada",
        subscriptionUpdateFailed: "No se pudo actualizar la suscripción",
      },
      suspendDialog: {
        title: "Suspender inquilino",
        descriptionLead: "¿Seguro que desea suspender a",
        descriptionTrail:
          "? El inquilino no podrá iniciar sesión ni acceder a datos hasta que se reactive.",
      },
      reactivateDialog: {
        title: "Reactivar inquilino",
        descriptionLead: "¿Seguro que desea reactivar a",
        descriptionTrail:
          "? El inquilino podrá iniciar sesión y acceder a datos de nuevo.",
      },
      suspend: "Suspender",
      suspending: "Suspendiendo…",
      reactivate: "Reactivar",
      reactivating: "Reactivando…",
      changePlan: {
        title: "Cambiar plan — {name}",
        description: "Actualice plan, estado o notas de facturación.",
        plan: "Plan",
        status: "Estado",
        billingNotes: "Notas de facturación (opcional)",
        billingNotesPlaceholder:
          "Problemas de pago, acuerdos personalizados, etc.",
      },
    },
    users: {
      page: {
        title: "Usuarios de la plataforma",
        description:
          "Administre todos los usuarios entre inquilinos (solo superusuario)",
      },
      createUser: "Crear usuario",
      searchPlaceholder: "Buscar por correo o usuario…",
      emptyMessage: "No se encontraron usuarios.",
      columns: {
        user: "Usuario",
        email: "Correo",
        status: "Estado",
        tenants: "Inquilinos",
        joined: "Alta",
      },
      userStatus: { active: "Activo", suspended: "Suspendido" },
      moreTenants: "+{count}",
      ariaImpersonate: "Suplantar",
      ariaResetPassword: "Restablecer contraseña",
      ariaSuspendUser: "Suspender usuario",
      toast: {
        userSuspended: "{username} ha sido suspendido",
        suspendFailed: "No se pudo suspender al usuario",
        passwordReset: "Contraseña restablecida",
        passwordResetFailed: "No se pudo restablecer la contraseña",
        impersonating: "Suplantando a {username}",
        impersonateFailed: "No se pudo suplantar",
        userCreated: "Usuario {username} creado",
        createFailed: "No se pudo crear el usuario",
      },
      suspendDialog: {
        title: "Suspender usuario",
        descriptionLead: "¿Seguro que desea suspender a",
        descriptionTrail:
          "? Perderá el acceso a todos los inquilinos. Se puede revertir editando el usuario.",
      },
      resetPassword: {
        title: "Restablecer contraseña",
        description:
          "Introduzca una nueva contraseña para este usuario. Mínimo 8 caracteres.",
        newPassword: "Nueva contraseña",
        placeholder: "Mín. 8 caracteres",
        resetting: "Restableciendo…",
        reset: "Restablecer",
      },
      createDialog: {
        title: "Crear usuario",
        description:
          "Cree un usuario nuevo y asígnelo opcionalmente a inquilinos.",
        username: "Usuario",
        email: "Correo",
        password: "Contraseña",
        defaultRole: "Rol predeterminado (inquilinos asignados)",
        assignTenants: "Asignar a inquilinos",
        placeholderUsername: "jdoe",
        placeholderEmail: "ana@ejemplo.com",
        placeholderPassword: "Mín. 8 caracteres",
        creating: "Creando…",
        create: "Crear",
      },
    },
    invitations: {
      page: {
        title: "Invitaciones",
        description:
          "Todas las invitaciones de inquilinos en la plataforma. Solo superusuario.",
      },
      emptyMessage: "No se encontraron invitaciones.",
      filterAllStatuses: "Todos los estados",
      filterStatusPlaceholder: "Estado",
      filterAllTenants: "Todos los inquilinos",
      filterTenantPlaceholder: "Inquilino",
      filterFrom: "Desde",
      filterTo: "Hasta",
      toast: {
        cancelled: "Invitación cancelada",
        cancelFailed: "No se pudo cancelar la invitación",
        resent: "Invitación reenviada correctamente",
        resendFailed: "No se pudo reenviar la invitación",
      },
      columns: {
        email: "Correo",
        tenant: "Inquilino",
        role: "Rol",
        status: "Estado",
        created: "Creada",
        expires: "Vence",
        invitedBy: "Invitó",
      },
      rowCancel: "Cancelar",
      rowResend: "Reenviar",
      status: {
        pending: "Pendiente",
        accepted: "Aceptada",
        cancelled: "Cancelada",
        expired: "Caducada",
      },
    },
  },
};

function patch(code, bundle) {
  const p = path.join(localesDir, `${code}.json`);
  const data = JSON.parse(readFileSync(p, "utf-8"));
  Object.assign(data, bundle);
  writeFileSync(p, `${JSON.stringify(data, null, 2)}\n`, "utf-8");
}

patch("fr", fr);
patch("es", es);
console.log("patched fr, es");
