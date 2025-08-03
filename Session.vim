let SessionLoad = 1
let s:so_save = &g:so | let s:siso_save = &g:siso | setg so=0 siso=0 | setl so=-1 siso=-1
let v:this_session=expand("<sfile>:p")
silent only
silent tabonly
cd ~/git/Dispatch
if expand('%') == '' && !&modified && line('$') <= 1 && getline(1) == ''
  let s:wipebuf = bufnr('%')
endif
let s:shortmess_save = &shortmess
if &shortmess =~ 'A'
  set shortmess=aoOA
else
  set shortmess=aoO
endif
badd +21 src/dispatch/dispatch.py
badd +15 pyproject.toml
badd +7 src/dispatch/tests/test_dispatcher_instances.py
badd +7 src/dispatch/tests/test_annotation_info.py
argglobal
%argdel
$argadd src/dispatch/dispatch.py
$argadd pyproject.toml
edit src/dispatch/tests/test_annotation_info.py
argglobal
if bufexists(fnamemodify("src/dispatch/tests/test_annotation_info.py", ":p")) | buffer src/dispatch/tests/test_annotation_info.py | else | edit src/dispatch/tests/test_annotation_info.py | endif
if &buftype ==# 'terminal'
  silent file src/dispatch/tests/test_annotation_info.py
endif
balt src/dispatch/tests/test_dispatcher_instances.py
setlocal foldmethod=indent
setlocal foldexpr=0
setlocal foldmarker={{{,}}}
setlocal foldignore=#
setlocal foldlevel=2
setlocal foldminlines=1
setlocal foldnestmax=20
setlocal foldenable
let s:l = 1 - ((0 * winheight(0) + 30) / 60)
if s:l < 1 | let s:l = 1 | endif
keepjumps exe s:l
normal! zt
keepjumps 1
normal! 028|
tabnext 1
if exists('s:wipebuf') && len(win_findbuf(s:wipebuf)) == 0 && getbufvar(s:wipebuf, '&buftype') isnot# 'terminal'
  silent exe 'bwipe ' . s:wipebuf
endif
unlet! s:wipebuf
set winheight=1 winwidth=20
let &shortmess = s:shortmess_save
let s:sx = expand("<sfile>:p:r")."x.vim"
if filereadable(s:sx)
  exe "source " . fnameescape(s:sx)
endif
let &g:so = s:so_save | let &g:siso = s:siso_save
set hlsearch
doautoall SessionLoadPost
unlet SessionLoad
" vim: set ft=vim :
