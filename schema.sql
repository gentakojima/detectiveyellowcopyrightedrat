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
  `keywords` varchar(512) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `grupos`
--

CREATE TABLE `grupos` (
  `id` bigint(20) NOT NULL,
  `title` varchar(120) NOT NULL,
  `spreadsheet` varchar(100) NOT NULL,
  `testgroup` TINYINT NOT NULL DEFAULT '0',
  `alerts` TINYINT NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `incursiones`
--

CREATE TABLE `incursiones` (
  `id` int(11) NOT NULL,
  `usuario_id` bigint(20) NOT NULL,
  `grupo_id` bigint(20) NOT NULL,
  `gimnasio_id` int(11) DEFAULT NULL,
  `time` varchar(5) NOT NULL,
  `endtime` varchar(5) DEFAULT NULL,
  `pokemon` varchar(20) NOT NULL,
  `gimnasio_text` varchar(60) DEFAULT NULL,
  `message` int(11) DEFAULT NULL,
  `edited` tinyint(4) NOT NULL DEFAULT '0',
  `cancelled` TINYINT NOT NULL DEFAULT '0',
  `addedtime` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ended` TINYINT NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `usuarios`
--

CREATE TABLE `usuarios` (
  `id` bigint(20) NOT NULL,
  `username` varchar(33) DEFAULT NULL,
  `level` int(11) DEFAULT NULL,
  `team` enum('Rojo','Azul','Amarillo','') DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `voy`
--

CREATE TABLE `voy` (
  `usuario_id` bigint(20) NOT NULL,
  `incursion_id` int(11) NOT NULL,
  `addedtime` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `plus` int(11) NOT NULL DEFAULT '0',
  `estoy` tinyint(4) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Table structure for table `alertas`
--

CREATE TABLE `alertas` (
  `id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `gimnasio_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


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
  ADD PRIMARY KEY (`id`);

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
