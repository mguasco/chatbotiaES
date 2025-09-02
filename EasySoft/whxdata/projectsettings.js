// Publish project specific data
(function() {
rh = window.rh;
model = rh.model;
var defaultTopic = "html/user_profile.htm";
rh._.exports(defaultTopic);
rh.consts('DEFAULT_TOPIC', encodeURI("html/user_profile.htm"));
rh.consts('HOME_FILEPATH', encodeURI('index.htm'));
rh.consts('START_FILEPATH', encodeURI('index.htm'));
rh.consts('HELP_ID', 'b4bcd671-cb57-4bac-950c-be6687ef8ce7' || 'preview');
rh.consts('LNG_SUBSTR_SEARCH', 0);

model.publish(rh.consts('KEY_LNG_NAME'), "es");
model.publish(rh.consts('KEY_DIR'), "ltr");
model.publish(rh.consts('KEY_LNG'), {"BreadcrumbStart":"Página principal:","BrsNextButton":"Siguiente","BrsPrevButton":"Anterior","CloseFavorites":"Cerrar favoritos","ContentsTab":"Contenido","CookiesAcceptText":"Le pedimos que acepte las cookies por motivos de rendimiento, legibilidad y experiencia. Las cookies se utilizan para marcar temas favoritos y para restaurar la tabla de contenido, el índice y el glosario con los cambios de tema. Este ajuste solo se pide una vez y puede revertirse borrando las cookies de navegador.","CookiesAcceptButton":"Aceptar","CookiesDenyButton":"Más tarde","EditFavorites":"Editar favoritos","FavoriteArticle":"artículo guardado","FavoriteArticles":"artículos guardados","Expand All":"Expandir todo","Filter":"Filtro","Select Bookmark":"Seleccionar marcador","Download PDF":"Descargar PDF","Search":"Buscar...","Share":"Compartir","Collapse All":"Contraer todo","Remove Highlight":"Quitar resaltado","Print":"Imprimir","Favorites":"Favoritos","FullScreenButton":"Pantalla completa","GlossaryTab":"Glosario","GlossResultHeaderLabel":"Diccionario del glosario","HideLeftPanelTip":"Ocultar panel izquierdo","HideResults":"Ocultar resultados","HomeButton":"Página principal","HomePageLogoTitle":"Logotipo","HomePageSubtitle":"EasySoft","IndexTab":"Índice","MCSearchResultShowFullTopic":"Más información...","MiniTOCCaption":"","NoResultsFoundText":"No se encontraron resultados","PrintButtonTip":"Imprimir","RemoveFavItem":"Quitar ","RemoveHighlight":"Quitar resaltado","ResultsFoundText":"%1 resultado(s) encontrado(s) para %2","SearchPlaceHolder":"¿Cómo podemos ayudarte?","IndexFilterKewords":"Filtrar palabras clave","GlossaryFilterTerms":"Filtrar términos","SetAsFavorite":"Establecer como favorito","ShowLeftPanelTip":"Mostrar panel izquierdo","TOCTileArticlesCount":"artículo(s)","ToTopButtonTip":"Ir al principio","UnsetAsFavorite":"Dejar de establecer como favorito","TopicHiddenText":"Este tema ha quedado fuera del filtro por los filtros seleccionados.","ResetFilters":"Restablecer filtros","SkipToMainContent":"Saltar al contenido principal","ClearSearchBox":"Borrar cuadro de búsqueda","RemoveFilter":"Quitar filtro","SelectedFilters":"Filtros seleccionados","CloseSidebar":"Cerrar barra lateral","OpenMenu":"Abrir menú","CloseMenu":"Cerrar menú","ViewMore":"Ver más","SearchPaginationLabel":"De %1 a %2 de %3 resultados","NextSearchResults":"Página de búsqueda siguiente","PrevSearchResults":"Página de búsqueda anterior"});

model.publish(rh.consts('KEY_HEADER_TITLE'), "Centro de Aprendizaje");
model.publish(rh.consts('PDF_FILE_NAME'), "");
model.publish(rh.consts('MAX_SEARCH_RESULTS'), "20");
model.publish(rh.consts('KEY_SKIN_FOLDER_NAME'), "Orange");
model.publish(rh.consts('CHAT_API_SESSION_TOKEN'), "");
model.publish(rh.consts('CHAT_API_PROJ_ID'), "");

model.publish(rh.consts('KEY_SUBSTR_SEARCH'), "");
model.publish(rh.consts('KEY_LOGO_URL'), "");
model.publish(rh.consts('KEY_SPECIAL_CHARS'), "0;1;2;3;4;5;6;7;8;9");
model.publish(rh.consts('SEARCH_PAGE'), "search.htm");
})();
