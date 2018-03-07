--
-- Database: `detectivepikachu`
--

-- --------------------------------------------------------

--
-- Table structure for table `gimnasios`
--

CREATE TABLE `gimnasios` (
  `id` int(11) NOT NULL,
  `grupo_id` bigint(11) NOT NULL,
  `name` varchar(128) NOT NULL,
  `latitude` varchar(20) NOT NULL,
  `longitude` varchar(20) NOT NULL,
  `keywords` varchar(512) NOT NULL,
  `tags` varchar(45) DEFAULT NULL,
  `zones` VARCHAR(256) DEFAULT NULL,
  `address` varchar(128) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `grupos`
--

CREATE TABLE `grupos` (
  `id` bigint(20) NOT NULL,
  `title` varchar(120) NOT NULL,
  `alias` varchar(60) DEFAULT NULL,
  `spreadsheet` varchar(100) DEFAULT NULL,
  `settings_message` bigint(20) DEFAULT NULL,
  `testgroup` TINYINT NOT NULL DEFAULT '0',
  `alerts` TINYINT NOT NULL DEFAULT '1',
  `disaggregated` TINYINT NOT NULL DEFAULT '0',
  `latebutton` TINYINT NOT NULL DEFAULT '0',
  `refloat` TINYINT NOT NULL DEFAULT '0',
  `refloatauto` TINYINT NOT NULL DEFAULT '0',
  `lastrefloatauto` datetime DEFAULT NULL,
  `candelete` TINYINT NOT NULL DEFAULT '1',
  `gotitbuttons` TINYINT NOT NULL DEFAULT '0',
  `locations` TINYINT NOT NULL DEFAULT '1',
  `gymcommand` TINYINT NOT NULL DEFAULT '0',
  `raidcommand` TINYINT NOT NULL DEFAULT '1',
  `raidcommandorder` TINYINT NOT NULL DEFAULT '1',
  `talkgroup` VARCHAR(60) NULL DEFAULT NULL,
  `babysitter` TINYINT NOT NULL DEFAULT '0',
  `timeformat` TINYINT NOT NULL DEFAULT '0',
  `icontheme` TINYINT NOT NULL DEFAULT '0',
  `listorder` TINYINT NOT NULL DEFAULT '0',
  `snail` TINYINT NOT NULL DEFAULT '1',
  `validationrequired` TINYINT NOT NULL DEFAULT '0',
  `plusmax` TINYINT NOT NULL DEFAULT '5',
  `plusdisaggregated` TINYINT NOT NULL DEFAULT '0',
  `plusdisaggregatedinline` TINYINT NOT NULL DEFAULT '0',
  `timezone` VARCHAR(60) NOT NULL DEFAULT 'Europe/Madrid',
  `rankingweek` TINYINT NOT NULL DEFAULT '10',
  `rankingmonth` TINYINT NOT NULL DEFAULT '15',
  `banned` TINYINT NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `incursiones`
--

CREATE TABLE `incursiones` (
  `id` int(11) NOT NULL,
  `usuario_id` bigint(20) DEFAULT NULL,
  `grupo_id` bigint(20) NOT NULL,
  `gimnasio_id` int(11) DEFAULT NULL,
  `pokemon` varchar(20) DEFAULT NULL,
  `egg` enum('N1', 'N2', 'N3', 'N4', 'N5', 'EX') DEFAULT NULL,
  `gimnasio_text` varchar(60) DEFAULT NULL,
  `message` int(11) DEFAULT NULL,
  `edited` tinyint(4) NOT NULL DEFAULT '0',
  `refloated` tinyint(4) NOT NULL DEFAULT '0',
  `addedtime` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `timeraid` timestamp NULL DEFAULT NULL,
  `timeend` datetime DEFAULT NULL,
  `status` enum('creating','waiting','started','ended','cancelled','deleted','old') NOT NULL DEFAULT 'waiting'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `usuarios`
--

CREATE TABLE `usuarios` (
  `id` bigint(20) NOT NULL,
  `username` varchar(33) DEFAULT NULL,
  `level` int(11) DEFAULT NULL,
  `team` enum('Rojo','Azul','Amarillo','') DEFAULT NULL,
  `banned` tinyint(4) NOT NULL DEFAULT '0',
  `trainername` varchar(20) DEFAULT NULL,
  `validation` enum('none','oak','internal') NOT NULL DEFAULT 'none',
  `validation_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `voy`
--

CREATE TABLE `voy` (
  `usuario_id` bigint(20) NOT NULL,
  `incursion_id` int(11) NOT NULL,
  `addedtime` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `novoy` TINYINT NOT NULL DEFAULT '0',
  `plus` int(11) NOT NULL DEFAULT '0',
  `plusr` int(11) NOT NULL DEFAULT '0',
  `plusb` int(11) NOT NULL DEFAULT '0',
  `plusy` int(11) NOT NULL DEFAULT '0',
  `estoy` tinyint(4) NOT NULL DEFAULT '0',
  `tarde` tinyint(4) NOT NULL DEFAULT '0',
  `lotengo` tinyint(4) NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Table structure for table `alertas`
--

CREATE TABLE `alertas` (
  `id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `gimnasio_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


--
-- Table structure for table `validaciones`
--

CREATE TABLE `validaciones` (
  `id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `startedtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `step` enum('waitingtrainername','waitingscreenshot','failed','expired','completed') NOT NULL DEFAULT 'waitingtrainername',
  `tries` int(11) NOT NULL DEFAULT '0',
  `pokemon` varchar(15) NOT NULL,
  `pokemonname` varchar(15) NOT NULL,
  `trainername` varchar(20) DEFAULT NULL,
  `team` enum('Azul','Rojo','Amarillo','') DEFAULT NULL,
  `level` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


--
-- Indexes for dumped tables
--

--
-- Indexes for table `gimnasios`
--
ALTER TABLE `gimnasios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `grupo_name_unique` (`grupo_id`,`name`),
  ADD KEY `grupo` (`grupo_id`);

--
-- Indexes for table `grupos`
--
ALTER TABLE `grupos`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `incursiones`
--
ALTER TABLE `incursiones`
  ADD PRIMARY KEY (`id`),
  ADD KEY `usuario_id` (`usuario_id`),
  ADD KEY `grupo_id` (`grupo_id`),
  ADD KEY `gimnasio_id` (`gimnasio_id`);

--
-- Indexes for table `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `trainername` (`trainername`),
  ADD UNIQUE KEY `username` (`username`),
  ADD KEY `validation_id` (`validation_id`);

--
-- Indexes for table `voy`
--
ALTER TABLE `voy`
  ADD PRIMARY KEY (`usuario_id`,`incursion_id`),
  ADD KEY `usuario_id` (`usuario_id`),
  ADD KEY `incursion_id` (`incursion_id`);

--
-- Indexes for table `alertas`
--
ALTER TABLE `alertas`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `usuario_id` (`usuario_id`,`gimnasio_id`) USING BTREE;

--
-- Indexes for table `validaciones`
--
ALTER TABLE `validaciones`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `gimnasios`
--
ALTER TABLE `gimnasios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=387;
--
-- AUTO_INCREMENT for table `incursiones`
--
ALTER TABLE `incursiones`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1020;

--
-- AUTO_INCREMENT for table `alertas`
--
ALTER TABLE `alertas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=18;

--
-- AUTO_INCREMENT for table `validaciones`
--
ALTER TABLE `validaciones`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;
COMMIT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `gimnasios`
--
ALTER TABLE `gimnasios`
  ADD CONSTRAINT `grupo` FOREIGN KEY (`grupo_id`) REFERENCES `grupos` (`id`);

--
-- Constraints for table `incursiones`
--
ALTER TABLE `incursiones`
  ADD CONSTRAINT `gimnasio` FOREIGN KEY (`gimnasio_id`) REFERENCES `gimnasios` (`id`),
  ADD CONSTRAINT `grupoincurs` FOREIGN KEY (`grupo_id`) REFERENCES `grupos` (`id`),
  ADD CONSTRAINT `usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Constraints for table `voy`
--
ALTER TABLE `voy`
  ADD CONSTRAINT `incursionvoy` FOREIGN KEY (`incursion_id`) REFERENCES `incursiones` (`id`),
  ADD CONSTRAINT `usuariovoy` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`);
