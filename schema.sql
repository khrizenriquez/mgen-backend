CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Catálogo de estados
CREATE TABLE status_catalog (
    id INT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Identidad y acceso
CREATE TABLE app_user (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX app_user_email_lower_uidx ON app_user (LOWER(email));

CREATE TABLE app_role (
    id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE app_user_role (
    user_id UUID NOT NULL,
    role_id INT NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES app_user(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES app_role(id) ON DELETE CASCADE
);

-- Donaciones
CREATE TABLE donation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    amount_gtq NUMERIC(12,2) NOT NULL CHECK (amount_gtq > 0),
    status_id INT NOT NULL REFERENCES status_catalog(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    paid_at TIMESTAMPTZ,
    donor_email TEXT NOT NULL,
    donor_name TEXT,
    donor_nit TEXT,
    user_id UUID REFERENCES app_user(id),
    payu_order_id TEXT,
    reference_code TEXT NOT NULL UNIQUE,
    correlation_id TEXT NOT NULL UNIQUE
);

-- Índices
CREATE INDEX donation_status_idx ON donation(status_id);
CREATE INDEX donation_donor_email_idx ON donation(donor_email);
CREATE INDEX donation_created_at_idx ON donation(created_at);
CREATE INDEX donation_status_created_at_idx ON donation(status_id, created_at);
CREATE INDEX app_user_role_role_user_idx ON app_user_role(role_id, user_id);

-- Eventos de pago
CREATE TABLE payment_event (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    donation_id UUID NOT NULL REFERENCES donation(id) ON DELETE RESTRICT,
    event_id TEXT NOT NULL UNIQUE,
    source TEXT NOT NULL CHECK (source IN ('webhook', 'recon')),
    status_id INT NOT NULL REFERENCES status_catalog(id),
    payload_raw JSONB NOT NULL DEFAULT '{}'::jsonb,
    signature_ok BOOLEAN NOT NULL DEFAULT FALSE,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX payment_event_donation_idx ON payment_event(donation_id);
CREATE INDEX payment_event_received_at_idx ON payment_event(received_at);

-- Logs de correo
CREATE TABLE email_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    donation_id UUID NOT NULL REFERENCES donation(id) ON DELETE RESTRICT,
    to_email TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('receipt', 'resend')),
    status_id INT NOT NULL REFERENCES status_catalog(id),
    provider_msg_id TEXT UNIQUE,
    attempt INT NOT NULL DEFAULT 0 CHECK (attempt >= 0),
    last_error TEXT,
    sent_at TIMESTAMPTZ,
    provider_event_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX email_log_donation_idx ON email_log(donation_id);
CREATE INDEX email_log_status_idx ON email_log(status_id);

-- Organizaciones
CREATE TABLE organization (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    address TEXT,
    website TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Agregar organización a usuarios
ALTER TABLE app_user ADD COLUMN organization_id UUID REFERENCES organization(id);

-- Perfil de Donante
CREATE TABLE donor_contact (
    user_id UUID PRIMARY KEY REFERENCES app_user(id) ON DELETE CASCADE,
    phone_number TEXT,
    address TEXT,
    contact_preference TEXT CHECK (contact_preference IN ('email', 'phone', 'mail')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Datos iniciales para status_catalog
INSERT INTO status_catalog (id, code, description) VALUES
  -- Donaciones
  (1,  'donation.pending',  'Donación pendiente'),
  (2,  'donation.approved', 'Donación aprobada'),
  (3,  'donation.declined', 'Donación rechazada'),
  (4,  'donation.expired',  'Donación expirada'),
  -- Email
  (10, 'email.queued',     'Email en cola'),
  (11, 'email.sent',       'Email enviado'),
  (12, 'email.failed',     'Email fallido'),
  (13, 'email.delivered',  'Email entregado'),
  (14, 'email.bounced',    'Email devuelto'),
  -- Eventos (webhook/recon)
  (20, 'event.pending',    'Evento pendiente'),
  (21, 'event.approved',   'Evento aprobado'),
  (22, 'event.declined',   'Evento rechazado'),
  (23, 'event.error',      'Evento con error')
ON CONFLICT (id) DO NOTHING;

-- Roles del sistema
INSERT INTO app_role (name, description) VALUES
('ADMIN', 'System administrator with full access to all organizations and data'),
('ORGANIZATION', 'Organization administrator with access to their own organization data'),
('AUDITOR', 'Read-only access for compliance and auditing purposes'),
('DONOR', 'Registered donor with access to their own donations and profile'),
('USER', 'Regular user with basic access')
ON CONFLICT (name) DO NOTHING;

-- Organización por defecto
INSERT INTO organization (id, name, description, contact_email, is_active) VALUES
('550e8400-e29b-41d4-a716-446655440000', 'Fundación Donaciones Guatemala', 'Organización principal de donaciones en Guatemala', 'contacto@donacionesgt.org', TRUE)
ON CONFLICT (id) DO NOTHING;
