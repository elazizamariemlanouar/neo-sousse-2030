-- Proprietaires
INSERT INTO proprietaire (nom, adresse, telephone, email) VALUES
('Neo Sousse Municipality', 'Central Street Sousse', '73100001', 'contact@neosousse.tn'),
('Green Energy Corp', 'Industrial Zone Sousse', '73100002', 'info@greenenergy.tn'),
('Smart Mobility Group', 'Technopole Sousse', '73100003', 'contact@smartmobility.tn'),
('Urban Sensors Ltd', 'Corniche Road Sousse', '73100004', 'support@urbansensors.tn');


-- Capteurs
INSERT INTO capteur (type_capteur, latitude, longitude, statut, id_proprietaire, date_installation) VALUES
('air_quality', 35.8256, 10.6369, 'active', 1, '2023-11-10'),
('air_quality', 35.8292, 10.6441, 'inactive', 4, '2024-03-18'),
('traffic', 35.8270, 10.6400, 'active', 1, '2024-01-05'),
('traffic', 35.8204, 10.6289, 'maintenance', 1, '2024-06-22'),
('energy', 35.8235, 10.6332, 'active', 2, '2024-08-14'),
('energy', 35.8180, 10.6295, 'inactive', 2, '2023-12-01'),
('waste', 35.8149, 10.6257, 'active', 1, '2025-01-20'),
('lighting', 35.8269, 10.6398, 'active', 4, '2025-02-02');


-- Citoyens
INSERT INTO citoyen (nom, adresse, email, score_ecologique, preference_mobilite) VALUES
('Ali Ben Ahmed', 'Habib Bourguiba Street', 'ali.ahmed@mail.com', 91.2, 'bike'),
('Meriem Trabelsi', 'Marina Road', 'meriem.t@mail.com', 88.5, 'public_transport'),
('Yassine Khemiri', 'Sahloul District', 'yassine.k@mail.com', 74.8, 'electric_car'),
('Ines Jlassi', 'Riadh City', 'ines.j@mail.com', 82.1, 'walking'),
('Omar Gharbi', 'Kantaoui Area', 'omar.g@mail.com', 66.4, 'bus'),
('Sami Ayari', 'Akouda Road', 'sami.a@mail.com', 59.9, 'car');

-- Techniciens
INSERT INTO technicien (nom, email, certification) VALUES
('Sami Khelifi', 'sami.k@tech.com', 'iot_sensors'),
('Leila Mansour', 'leila.m@tech.com', 'advanced_maintenance'),
('Karim Ben Salah', 'karim.b@tech.com', 'network_specialist'),
('Nour Chatti', 'nour.c@tech.com', 'energy_systems');


-- Interventions
INSERT INTO intervention (id_capteur, date_intervention, type_intervention, duree, cout, economie_co2) VALUES
(1, '2025-11-15 09:30', 'predictive', 90, 120.00, 8.5),
(2, '2025-11-28 14:10', 'corrective', 140, 260.00, 5.2),
(3, '2025-12-02 08:45', 'predictive', 60, 95.00, 6.8),
(4, '2025-12-06 16:20', 'curative', 180, 320.00, 3.1),
(5, '2025-12-10 10:00', 'predictive', 75, 110.00, 9.4),
(7, '2025-12-12 13:30', 'corrective', 120, 180.00, 4.6);

-- Intervention-Technicien
INSERT INTO intervention_technicien (id_intervention, id_technicien, role) VALUES
(1, 1, 'intervenant'),
(1, 2, 'validator'),
(2, 3, 'intervenant'),
(3, 1, 'intervenant'),
(4, 2, 'intervenant'),
(5, 4, 'intervenant'),
(6, 3, 'intervenant');

-- Mesures
INSERT INTO mesure (id_capteur, date_mesure, type_mesure, valeur) VALUES
-- Air quality
(1, '2025-12-17 06:00', 'AQI', 38),
(1, '2025-12-17 08:00', 'AQI', 61),
(1, '2025-12-17 10:00', 'AQI', 74),
(2, '2025-12-17 12:00', 'AQI', 52),

-- Traffic
(3, '2025-12-17 07:30', 'vehicles_per_hour', 420),
(3, '2025-12-17 08:30', 'vehicles_per_hour', 760),
(3, '2025-12-17 18:00', 'vehicles_per_hour', 820),

-- Energy
(5, '2025-12-17 09:00', 'kwh', 350),
(5, '2025-12-17 12:00', 'kwh', 510),
(6, '2025-12-17 15:00', 'kwh', 280),

-- Waste
(7, '2025-12-17 10:00', 'fill_level', 65),
(7, '2025-12-17 16:00', 'fill_level', 92),

-- Lighting
(8, '2025-12-17 05:30', 'lux', 45),
(8, '2025-12-17 19:00', 'lux', 210);


-- Véhicules
INSERT INTO vehicule (plaque, type_vehicule, energie) VALUES
('TN-1001', 'electric_shuttle', 'electric'),
('TN-1002', 'city_bus', 'hydrogen'),
('TN-1003', 'waste_truck', 'hybrid'),
('TN-1004', 'service_van', 'diesel');


-- Trajets
INSERT INTO trajet (id_vehicule, origine, destination, date_trajet, economie_co2) VALUES
(1, 'Central Square', 'ENISo University', '2025-12-17 08:30', 3.6),
(2, 'Bus Station', 'City Center', '2025-12-17 09:10', 5.4),
(3, 'Industrial Zone', 'Municipal Dump', '2025-12-16 06:15', 2.1),
(1, 'ENISo University', 'Sahloul', '2025-12-17 17:45', 4.0),
(4, 'City Hall', 'Maintenance Center', '2025-12-15 11:20', 1.2);
